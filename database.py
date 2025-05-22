"""
Tainment+ Discord Bot - Database Operations

This module handles all database operations for the Tainment+ Discord bot,
including user subscription tracking and management.
"""

import aiosqlite
import logging
import os
from datetime import datetime, timedelta

import config

logger = logging.getLogger("tainment_bot.database")

async def init_db():
    """Initialize the database and create necessary tables if they don't exist."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Create users table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create subscriptions table with enhanced fields
        await db.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tier TEXT NOT NULL,
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            active BOOLEAN DEFAULT TRUE,
            transaction_id TEXT,
            payment_method TEXT,
            grace_period_end TIMESTAMP,
            renewal_reminder_sent BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create subscription_history table to track changes
        await db.execute('''
        CREATE TABLE IF NOT EXISTS subscription_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            previous_tier TEXT NOT NULL,
            new_tier TEXT NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            admin_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create usage_stats table for tracking feature usage
        await db.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            feature TEXT NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create game_scores table for leaderboards
        await db.execute('''
        CREATE TABLE IF NOT EXISTS game_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create story_progress table to track user progress in multi-part stories
        await db.execute('''
        CREATE TABLE IF NOT EXISTS story_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            story_name TEXT NOT NULL,
            current_part INTEGER NOT NULL DEFAULT 1,
            last_read TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Create payment_transactions table
        await db.execute('''
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT NOT NULL,
            tier TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        await db.commit()
        logger.info("Database initialized successfully")

async def get_user(user_id):
    """Get user information from the database."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        )
        return await cursor.fetchone()

async def add_user(user_id, username):
    """Add a new user to the database."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Check if user already exists
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE user_id = ?", 
            (user_id,)
        )
        existing_user = await cursor.fetchone()
        
        if not existing_user:
            await db.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()
            logger.info(f"Added new user: {username} (ID: {user_id})")
            
            # Add default Basic subscription
            await add_subscription(user_id, "Basic")
            return True
        return False

async def get_subscription(user_id):
    """Get the current active subscription for a user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND active = TRUE
            ORDER BY end_date DESC LIMIT 1
            """, 
            (user_id,)
        )
        return await cursor.fetchone()

async def add_subscription(user_id, tier, duration_days=30, transaction_id=None, payment_method=None):
    """
    Add a new subscription for a user.
    
    Args:
        user_id: Discord user ID
        tier: Subscription tier
        duration_days: Duration in days
        transaction_id: Optional transaction ID for payment tracking
        payment_method: Optional payment method used
        
    Returns:
        bool: Whether the subscription was successfully added
    """
    # Calculate end date
    end_date = None
    grace_period_end = None
    
    if tier != "Basic":  # Basic tier doesn't expire
        end_date = (datetime.now() + timedelta(days=duration_days)).isoformat()
        # Grace period is 3 days after subscription ends
        grace_period_end = (datetime.now() + timedelta(days=duration_days + 3)).isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Deactivate any existing subscriptions
        await db.execute(
            "UPDATE subscriptions SET active = FALSE WHERE user_id = ? AND active = TRUE",
            (user_id,)
        )
        
        # Add new subscription
        await db.execute(
            """
            INSERT INTO subscriptions (
                user_id, tier, end_date, active, 
                transaction_id, payment_method, grace_period_end
            )
            VALUES (?, ?, ?, TRUE, ?, ?, ?)
            """,
            (user_id, tier, end_date, transaction_id, payment_method, grace_period_end)
        )
        
        # If there's a transaction ID, log the payment transaction
        if transaction_id and tier != "Basic":
            # Get the price for this tier
            price = config.SUBSCRIPTION_TIERS[tier]["price"] * (duration_days / 30)
            
            await db.execute(
                """
                INSERT INTO payment_transactions (
                    transaction_id, user_id, amount, status, 
                    tier, duration_days, completed_at
                )
                VALUES (?, ?, ?, 'completed', ?, ?, CURRENT_TIMESTAMP)
                """,
                (transaction_id, user_id, price, tier, duration_days)
            )
        
        await db.commit()
        logger.info(f"Added {tier} subscription for user ID: {user_id}")
        return True

async def update_subscription(user_id, new_tier, duration_days=30, transaction_id=None, payment_method=None, admin_id=None, reason=None):
    """
    Update a user's subscription to a new tier.
    
    Args:
        user_id: Discord user ID
        new_tier: New subscription tier
        duration_days: Duration in days
        transaction_id: Optional transaction ID for payment tracking
        payment_method: Optional payment method used
        admin_id: Optional admin user ID if this was an admin action
        reason: Optional reason for the change
        
    Returns:
        bool: Whether the subscription was successfully updated
    """
    # Get current subscription
    current_subscription = await get_subscription(user_id)
    previous_tier = current_subscription["tier"] if current_subscription else "None"
    
    # Add new subscription
    success = await add_subscription(user_id, new_tier, duration_days, transaction_id, payment_method)
    
    if success:
        # Log subscription history
        await log_subscription_change(user_id, previous_tier, new_tier, admin_id, reason)
        return True
    return False

async def log_feature_usage(user_id, feature):
    """Log usage of a feature by a user."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "INSERT INTO usage_stats (user_id, feature) VALUES (?, ?)",
            (user_id, feature)
        )
        await db.commit()
        return True

async def check_subscription_access(user_id, feature_tier):
    """
    Check if a user has access to a feature based on their subscription tier.
    
    Args:
        user_id: The Discord user ID
        feature_tier: The minimum tier required for the feature ('Basic', 'Premium', or 'Pro')
    
    Returns:
        bool: True if the user has access, False otherwise
    """
    tier_levels = {
        "Basic": 0,
        "Premium": 1,
        "Pro": 2
    }
    
    subscription = await get_subscription(user_id)
    if not subscription:
        # If no subscription found, add a Basic one
        await add_user(user_id, "Unknown")  # Username will be updated on first command
        return tier_levels.get("Basic", 0) >= tier_levels.get(feature_tier, 0)
    
    # Check if subscription is expired
    if subscription["end_date"] and subscription["tier"] != "Basic":
        end_date = datetime.fromisoformat(subscription["end_date"])
        if end_date < datetime.now():
            # Subscription expired, downgrade to Basic
            await add_subscription(user_id, "Basic")
            return tier_levels.get("Basic", 0) >= tier_levels.get(feature_tier, 0)
    
    # Check if user's tier level is sufficient
    user_tier_level = tier_levels.get(subscription["tier"], 0)
    required_tier_level = tier_levels.get(feature_tier, 0)
    
    return user_tier_level >= required_tier_level

async def update_game_score(user_id, game_name, score):
    """
    Update a user's score for a specific game.
    Only updates if the new score is higher than their previous best.
    
    Args:
        user_id: The Discord user ID
        game_name: The name of the game
        score: The score achieved
        
    Returns:
        tuple: (bool, int) - Whether the score was updated and the user's best score
    """
    # Get the user's current best score
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT MAX(score) as best_score
            FROM game_scores
            WHERE user_id = ? AND game_name = ?
            """,
            (user_id, game_name)
        )
        result = await cursor.fetchone()
        best_score = result['best_score'] if result and result['best_score'] is not None else 0
        
        # Only update if the new score is higher
        if score > best_score:
            await db.execute(
                """
                INSERT INTO game_scores (user_id, game_name, score)
                VALUES (?, ?, ?)
                """,
                (user_id, game_name, score)
            )
            await db.commit()
            logger.info(f"Updated score for user {user_id} in game {game_name}: {score}")
            return True, score
        
        return False, best_score

async def get_leaderboard(game_name, limit=10):
    """
    Get the leaderboard for a specific game.
    
    Args:
        game_name: The name of the game
        limit: Maximum number of entries to return (default: 10)
        
    Returns:
        list: List of tuples (user_id, score) sorted by score (highest first)
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT user_id, MAX(score) as best_score
            FROM game_scores
            WHERE game_name = ?
            GROUP BY user_id
            ORDER BY best_score DESC
            LIMIT ?
            """,
            (game_name, limit)
        )
        results = await cursor.fetchall()
        return [(row['user_id'], row['best_score']) for row in results]

async def get_available_games():
    """Get a list of all games that have scores recorded."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT DISTINCT game_name
            FROM game_scores
            ORDER BY game_name
            """
        )
        results = await cursor.fetchall()
        return [row['game_name'] for row in results]

async def update_story_progress(user_id, story_name, part):
    """Update a user's progress in a multi-part story."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        # Check if progress record exists
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id FROM story_progress
            WHERE user_id = ? AND story_name = ?
            """,
            (user_id, story_name)
        )
        result = await cursor.fetchone()
        
        if result:
            # Update existing record
            await db.execute(
                """
                UPDATE story_progress
                SET current_part = ?, last_read = CURRENT_TIMESTAMP
                WHERE user_id = ? AND story_name = ?
                """,
                (part, user_id, story_name)
            )
        else:
            # Create new record
            await db.execute(
                """
                INSERT INTO story_progress (user_id, story_name, current_part)
                VALUES (?, ?, ?)
                """,
                (user_id, story_name, part)
            )
        
        await db.commit()
        return True

async def get_story_progress(user_id, story_name):
    """Get a user's progress in a multi-part story."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT current_part, last_read
            FROM story_progress
            WHERE user_id = ? AND story_name = ?
            """,
            (user_id, story_name)
        )
        result = await cursor.fetchone()
        
        if result:
            return {
                "current_part": result["current_part"],
                "last_read": result["last_read"]
            }
        else:
            return {
                "current_part": 1,
                "last_read": None
            }

async def get_feature_usage_stats(feature=None, days=30):
    """
    Get usage statistics for features.
    
    Args:
        feature: Optional specific feature to get stats for
        days: Number of days to look back
        
    Returns:
        dict: Dictionary with feature usage counts
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        if feature:
            # Get stats for a specific feature
            cursor = await db.execute(
                """
                SELECT COUNT(*) as count, 
                       COUNT(DISTINCT user_id) as unique_users
                FROM usage_stats
                WHERE feature = ? AND used_at >= ?
                """,
                (feature, start_date)
            )
            result = await cursor.fetchone()
            
            return {
                "feature": feature,
                "count": result["count"],
                "unique_users": result["unique_users"]
            }
        else:
            # Get stats for all features
            cursor = await db.execute(
                """
                SELECT feature, 
                       COUNT(*) as count, 
                       COUNT(DISTINCT user_id) as unique_users
                FROM usage_stats
                WHERE used_at >= ?
                GROUP BY feature
                ORDER BY count DESC
                """,
                (start_date,)
            )
            results = await cursor.fetchall()
            
            return {
                row["feature"]: {
                    "count": row["count"],
                    "unique_users": row["unique_users"]
                } for row in results
            }



async def log_subscription_change(user_id, previous_tier, new_tier, admin_id=None, reason=None):
    """
    Log a subscription change in the subscription_history table.
    
    Args:
        user_id: Discord user ID
        previous_tier: Previous subscription tier
        new_tier: New subscription tier
        admin_id: Optional admin user ID if this was an admin action
        reason: Optional reason for the change
        
    Returns:
        bool: Whether the history was successfully logged
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO subscription_history (
                user_id, previous_tier, new_tier, admin_id, reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, previous_tier, new_tier, admin_id, reason)
        )
        await db.commit()
        logger.info(f"Logged subscription change for user {user_id}: {previous_tier} -> {new_tier}")
        return True

async def get_subscription_history(user_id, limit=10):
    """
    Get subscription history for a user.
    
    Args:
        user_id: Discord user ID
        limit: Maximum number of history entries to return
        
    Returns:
        list: List of subscription history entries
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM subscription_history
            WHERE user_id = ?
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def check_expiring_subscriptions(days_threshold=3):
    """
    Check for subscriptions that are about to expire within the specified threshold.
    
    Args:
        days_threshold: Number of days before expiration to check
        
    Returns:
        list: List of subscriptions about to expire
    """
    threshold_date = (datetime.now() + timedelta(days=days_threshold)).isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT s.*, u.username
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.active = TRUE
            AND s.tier != 'Basic'
            AND s.end_date <= ?
            AND s.end_date > CURRENT_TIMESTAMP
            AND s.renewal_reminder_sent = FALSE
            """,
            (threshold_date,)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def mark_renewal_reminder_sent(subscription_id):
    """
    Mark a subscription as having had a renewal reminder sent.
    
    Args:
        subscription_id: ID of the subscription
        
    Returns:
        bool: Whether the update was successful
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            UPDATE subscriptions
            SET renewal_reminder_sent = TRUE
            WHERE id = ?
            """,
            (subscription_id,)
        )
        await db.commit()
        return True

async def check_expired_subscriptions():
    """
    Check for subscriptions that have expired but are still within the grace period.
    
    Returns:
        list: List of expired subscriptions within grace period
    """
    current_time = datetime.now().isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT s.*, u.username
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.active = TRUE
            AND s.tier != 'Basic'
            AND s.end_date < ?
            AND s.grace_period_end > ?
            """,
            (current_time, current_time)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def check_grace_period_expired_subscriptions():
    """
    Check for subscriptions where the grace period has expired.
    These should be downgraded to Basic.
    
    Returns:
        list: List of subscriptions with expired grace periods
    """
    current_time = datetime.now().isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT s.*, u.username
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.active = TRUE
            AND s.tier != 'Basic'
            AND s.grace_period_end < ?
            """,
            (current_time,)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def downgrade_expired_subscriptions():
    """
    Downgrade subscriptions that have expired beyond the grace period to Basic tier.
    
    Returns:
        int: Number of subscriptions downgraded
    """
    expired_subscriptions = await check_grace_period_expired_subscriptions()
    count = 0
    
    for subscription in expired_subscriptions:
        # Downgrade to Basic
        success = await update_subscription(
            subscription["user_id"],
            "Basic",
            reason="Subscription expired beyond grace period"
        )
        
        if success:
            count += 1
    
    return count

async def extend_subscription(user_id, additional_days, admin_id=None, reason=None):
    """
    Extend a user's subscription by a specified number of days.
    
    Args:
        user_id: Discord user ID
        additional_days: Number of days to extend the subscription
        admin_id: Optional admin user ID who performed this action
        reason: Optional reason for the extension
        
    Returns:
        bool: Whether the extension was successful
    """
    # Get current subscription
    subscription = await get_subscription(user_id)
    
    if not subscription or subscription["tier"] == "Basic":
        logger.warning(f"Cannot extend Basic subscription for user {user_id}")
        return False
    
    # Calculate new end date
    current_end_date = datetime.fromisoformat(subscription["end_date"])
    new_end_date = (current_end_date + timedelta(days=additional_days)).isoformat()
    new_grace_period_end = (current_end_date + timedelta(days=additional_days + 3)).isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            """
            UPDATE subscriptions
            SET end_date = ?, grace_period_end = ?
            WHERE id = ?
            """,
            (new_end_date, new_grace_period_end, subscription["id"])
        )
        
        # Log the extension in history
        await db.execute(
            """
            INSERT INTO subscription_history (
                user_id, previous_tier, new_tier, admin_id, reason
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, subscription["tier"], subscription["tier"], admin_id, 
             reason or f"Extended subscription by {additional_days} days")
        )
        
        await db.commit()
        logger.info(f"Extended subscription for user {user_id} by {additional_days} days")
        return True

async def get_all_subscribers(tier=None, active_only=True):
    """
    Get all subscribers, optionally filtered by tier.
    
    Args:
        tier: Optional tier to filter by
        active_only: Whether to only include active subscriptions
        
    Returns:
        list: List of subscribers
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = """
            SELECT s.*, u.username
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE 1=1
        """
        params = []
        
        if active_only:
            query += " AND s.active = TRUE"
        
        if tier:
            query += " AND s.tier = ?"
            params.append(tier)
        
        query += " ORDER BY s.start_date DESC"
        
        cursor = await db.execute(query, params)
        results = await cursor.fetchall()
        return [dict(row) for row in results]

async def get_subscription_metrics(days=30):
    """
    Get subscription metrics for reporting.
    
    Args:
        days: Number of days to look back for changes
        
    Returns:
        dict: Dictionary with subscription metrics
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get current subscriber counts by tier
        cursor = await db.execute(
            """
            SELECT tier, COUNT(*) as count
            FROM subscriptions
            WHERE active = TRUE
            GROUP BY tier
            """
        )
        tier_counts = {row["tier"]: row["count"] for row in await cursor.fetchall()}
        
        # Get new subscriptions in the period
        cursor = await db.execute(
            """
            SELECT COUNT(*) as count
            FROM subscription_history
            WHERE previous_tier = 'None'
            AND changed_at >= ?
            """,
            (start_date,)
        )
        new_subscribers = (await cursor.fetchone())["count"]
        
        # Get upgrades in the period
        cursor = await db.execute(
            """
            SELECT COUNT(*) as count
            FROM subscription_history
            WHERE previous_tier != new_tier
            AND previous_tier != 'None'
            AND changed_at >= ?
            """,
            (start_date,)
        )
        upgrades = (await cursor.fetchone())["count"]
        
        # Get downgrades in the period
        cursor = await db.execute(
            """
            SELECT COUNT(*) as count
            FROM subscription_history
            WHERE previous_tier != 'Basic'
            AND new_tier = 'Basic'
            AND reason LIKE '%expired%'
            AND changed_at >= ?
            """,
            (start_date,)
        )
        expirations = (await cursor.fetchone())["count"]
        
        return {
            "subscribers_by_tier": tier_counts,
            "total_subscribers": sum(tier_counts.values()),
            "new_subscribers": new_subscribers,
            "upgrades": upgrades,
            "expirations": expirations,
            "period_days": days
        }

async def record_payment_transaction(transaction_id, user_id, amount, status, tier, duration_days):
    """
    Record a payment transaction.
    
    Args:
        transaction_id: Unique transaction ID
        user_id: Discord user ID
        amount: Payment amount
        status: Transaction status
        tier: Subscription tier
        duration_days: Subscription duration in days
        
    Returns:
        bool: Whether the transaction was successfully recorded
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO payment_transactions (
                    transaction_id, user_id, amount, status, 
                    tier, duration_days, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (transaction_id, user_id, amount, status, tier, duration_days)
            )
            await db.commit()
            logger.info(f"Recorded payment transaction: {transaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error recording payment transaction: {e}")
            return False

async def get_user_payment_history(user_id, limit=10):
    """
    Get payment history for a user.
    
    Args:
        user_id: Discord user ID
        limit: Maximum number of transactions to return
        
    Returns:
        list: List of payment transactions
    """
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT *
            FROM payment_transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )
        results = await cursor.fetchall()
        return [dict(row) for row in results]
