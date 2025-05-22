"""
Tainment+ Discord Bot - Subscription Tasks

This module handles scheduled tasks related to subscription management,
such as checking for expiring subscriptions and sending renewal notifications.
"""

import logging
import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta

import database
import config

logger = logging.getLogger("tainment_bot.subscription_tasks")

class SubscriptionTasks(commands.Cog):
    """Cog for handling subscription-related scheduled tasks."""
    
    def __init__(self, bot):
        self.bot = bot
        self.check_expiring_subscriptions.start()
        self.check_expired_subscriptions.start()
        logger.info("Subscription tasks initialized")
    
    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.check_expiring_subscriptions.cancel()
        self.check_expired_subscriptions.cancel()
    
    @tasks.loop(hours=24)
    async def check_expiring_subscriptions(self):
        """
        Check for subscriptions that are about to expire and send renewal notifications.
        Runs once per day.
        """
        logger.info("Checking for expiring subscriptions...")
        
        # Get subscriptions expiring in the next 3 days
        expiring_subscriptions = await database.check_expiring_subscriptions(days_threshold=3)
        
        for subscription in expiring_subscriptions:
            user_id = subscription["user_id"]
            username = subscription["username"]
            tier = subscription["tier"]
            end_date = datetime.fromisoformat(subscription["end_date"])
            days_left = (end_date - datetime.now()).days + 1
            
            try:
                # Try to get the user
                user = self.bot.get_user(user_id)
                
                if user:
                    # Create the notification embed
                    embed = discord.Embed(
                        title="Subscription Expiring Soon",
                        description=f"Your **{tier}** subscription will expire in **{days_left}** days.",
                        color=discord.Color.gold()
                    )
                    
                    embed.add_field(
                        name="Expiration Date",
                        value=end_date.strftime("%Y-%m-%d %H:%M"),
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Renewal Options",
                        value=f"Use `{config.COMMAND_PREFIX}renew` to renew your subscription and keep your premium benefits.",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Grace Period",
                        value="You'll have a 3-day grace period after expiration during which your premium features will still work.",
                        inline=False
                    )
                    
                    # Send the DM
                    await user.send(embed=embed)
                    logger.info(f"Sent expiration notification to {username} (ID: {user_id})")
                    
                    # Mark the reminder as sent
                    await database.mark_renewal_reminder_sent(subscription["id"])
                else:
                    logger.warning(f"Could not find user {username} (ID: {user_id}) to send expiration notification")
            
            except Exception as e:
                logger.error(f"Error sending expiration notification to {username} (ID: {user_id}): {e}")
    
    @check_expiring_subscriptions.before_loop
    async def before_check_expiring_subscriptions(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()
    
    @tasks.loop(hours=12)
    async def check_expired_subscriptions(self):
        """
        Check for expired subscriptions and handle grace periods.
        Runs twice per day.
        """
        logger.info("Checking for expired subscriptions...")
        
        # Check for subscriptions in grace period
        grace_period_subscriptions = await database.check_expired_subscriptions()
        
        for subscription in grace_period_subscriptions:
            user_id = subscription["user_id"]
            username = subscription["username"]
            tier = subscription["tier"]
            grace_end = datetime.fromisoformat(subscription["grace_period_end"])
            hours_left = int((grace_end - datetime.now()).total_seconds() / 3600)
            
            logger.info(f"Subscription for {username} (ID: {user_id}) is in grace period. {hours_left} hours left.")
        
        # Check for and downgrade subscriptions with expired grace periods
        downgraded_count = await database.downgrade_expired_subscriptions()
        
        if downgraded_count > 0:
            logger.info(f"Downgraded {downgraded_count} expired subscriptions to Basic tier")
    
    @check_expired_subscriptions.before_loop
    async def before_check_expired_subscriptions(self):
        """Wait until the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

def setup(bot):
    """Add the subscription tasks cog to the bot."""
    bot.add_cog(SubscriptionTasks(bot))
