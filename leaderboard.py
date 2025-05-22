"""
Tainment+ Discord Bot - Leaderboard System

This module handles the leaderboard functionality for games in the Tainment+ Discord bot,
including storing and retrieving game scores from the database.
"""

import discord
import logging
import asyncio
from datetime import datetime

import database

logger = logging.getLogger("tainment_bot.leaderboard")

async def init_leaderboard_db():
    """Initialize the leaderboard database tables."""
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        # Create game_scores table
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
        
        await db.commit()
        logger.info("Leaderboard database initialized successfully")

async def update_score(user_id, game_name, score):
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
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
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

async def get_user_best_score(user_id, game_name):
    """Get a user's best score for a specific game."""
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT MAX(score) as best_score
            FROM game_scores
            WHERE user_id = ? AND game_name = ?
            """,
            (user_id, game_name)
        )
        result = await cursor.fetchone()
        return result['best_score'] if result and result['best_score'] is not None else 0

async def get_leaderboard(game_name, limit=10):
    """
    Get the leaderboard for a specific game.
    
    Args:
        game_name: The name of the game
        limit: Maximum number of entries to return (default: 10)
        
    Returns:
        list: List of tuples (user_id, score) sorted by score (highest first)
    """
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
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

async def get_user_rank(user_id, game_name):
    """
    Get a user's rank on the leaderboard for a specific game.
    
    Args:
        user_id: The Discord user ID
        game_name: The name of the game
        
    Returns:
        int: The user's rank (1-based, 0 if not on leaderboard)
    """
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
        
        # Get all scores for this game, ordered by score
        cursor = await db.execute(
            """
            SELECT user_id, MAX(score) as best_score
            FROM game_scores
            WHERE game_name = ?
            GROUP BY user_id
            ORDER BY best_score DESC
            """,
            (game_name,)
        )
        results = await cursor.fetchall()
        
        # Find the user's position
        for i, row in enumerate(results, 1):
            if row['user_id'] == user_id:
                return i
        
        return 0  # User not found on leaderboard

async def get_available_games():
    """Get a list of all games that have scores recorded."""
    async with database.aiosqlite.connect(database.config.DB_PATH) as db:
        db.row_factory = database.aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT DISTINCT game_name
            FROM game_scores
            ORDER BY game_name
            """
        )
        results = await cursor.fetchall()
        return [row['game_name'] for row in results]

async def format_leaderboard_embed(ctx, game_name, entries=None):
    """
    Create a formatted embed for a game leaderboard.
    
    Args:
        ctx: The Discord context
        game_name: The name of the game
        entries: Optional pre-fetched leaderboard entries
        
    Returns:
        discord.Embed: The formatted leaderboard embed
    """
    # Get leaderboard entries if not provided
    if entries is None:
        entries = await get_leaderboard(game_name)
    
    if not entries:
        embed = discord.Embed(
            title=f"Leaderboard: {game_name.replace('_', ' ').title()}",
            description="No scores recorded yet. Be the first to play!",
            color=discord.Color.gold()
        )
        return embed
    
    # Create embed
    embed = discord.Embed(
        title=f"Leaderboard: {game_name.replace('_', ' ').title()}",
        description="Top players and their scores:",
        color=discord.Color.gold()
    )
    
    # Add user's rank if they're on the leaderboard
    user_rank = await get_user_rank(ctx.author.id, game_name)
    if user_rank > 0:
        user_score = await get_user_best_score(ctx.author.id, game_name)
        embed.description += f"\n\nYour rank: #{user_rank} (Score: {user_score})"
    
    # Add leaderboard entries
    for i, (user_id, score) in enumerate(entries, 1):
        # Try to get username from bot's cache
        user = ctx.bot.get_user(user_id)
        username = user.name if user else f"User {user_id}"
        
        # Add medal emoji for top 3
        prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        embed.add_field(
            name=f"{prefix} {username}",
            value=f"Score: {score}",
            inline=False
        )
    
    return embed

# Command to view leaderboards
async def leaderboard_command(ctx, game_name=None):
    """View the leaderboard for a specific game or all games."""
    # If no game specified, show list of available games
    if not game_name:
        available_games = await get_available_games()
        
        if not available_games:
            await ctx.send("No game scores recorded yet. Play some games to get on the leaderboard!")
            return
        
        embed = discord.Embed(
            title="Game Leaderboards",
            description="Select a game to view its leaderboard:",
            color=discord.Color.gold()
        )
        
        for game in available_games:
            # Format game name for display
            display_name = game.replace("_", " ").title()
            embed.add_field(
                name=display_name,
                value=f"Use `{ctx.prefix}leaderboard {game}` to view",
                inline=True
            )
        
        await ctx.send(embed=embed)
        return
    
    # Normalize game name
    game_name = game_name.lower().replace(" ", "_")
    
    # Check if game exists
    available_games = await get_available_games()
    if game_name not in available_games:
        # Check for partial matches
        matches = [g for g in available_games if game_name in g]
        if matches:
            embed = discord.Embed(
                title="Game Not Found",
                description=f"Did you mean one of these games?",
                color=discord.Color.orange()
            )
            for match in matches:
                embed.add_field(
                    name=match.replace("_", " ").title(),
                    value=f"Use `{ctx.prefix}leaderboard {match}`",
                    inline=True
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"No scores recorded for game '{game_name}'. Play the game to get on the leaderboard!")
        return
    
    # Get and display leaderboard
    leaderboard_embed = await format_leaderboard_embed(ctx, game_name)
    await ctx.send(embed=leaderboard_embed)

# Initialize the module
def setup(bot):
    """Set up the leaderboard module."""
    # Register the leaderboard command
    bot.add_command(discord.ext.commands.Command(
        leaderboard_command,
        name="leaderboard",
        aliases=["lb", "scores", "rankings"],
        help="View the leaderboard for a specific game or all games."
    ))
    
    # Initialize the database tables
    bot.loop.create_task(init_leaderboard_db())
    
    logger.info("Leaderboard module loaded")
