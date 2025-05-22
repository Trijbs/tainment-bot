"""
Tainment+ Discord Bot - Admin Subscription Commands

This module provides admin commands for managing user subscriptions,
including viewing subscribers, manually upgrading/downgrading users,
extending subscription periods, and generating reports.
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
import io
import csv

import config
import database

logger = logging.getLogger("tainment_bot.admin_subscription")

class AdminSubscription(commands.Cog):
    """Admin commands for subscription management."""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if the user has admin permissions."""
        if not ctx.guild:
            return False
        return ctx.author.guild_permissions.administrator
    
    @commands.command(name="subscribers")
    async def list_subscribers(self, ctx, tier=None):
        """
        List all subscribers, optionally filtered by tier.
        
        Usage: !subscribers [tier]
        """
        if tier and tier.capitalize() not in config.SUBSCRIPTION_TIERS:
            await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
            return
        
        tier_filter = tier.capitalize() if tier else None
        subscribers = await database.get_all_subscribers(tier=tier_filter)
        
        if not subscribers:
            await ctx.send("No subscribers found." if not tier else f"No subscribers found for tier: {tier_filter}")
            return
        
        # Create paginated embeds for the subscriber list
        embeds = []
        subscribers_per_page = 10
        
        for i in range(0, len(subscribers), subscribers_per_page):
            page_subscribers = subscribers[i:i+subscribers_per_page]
            
            embed = discord.Embed(
                title=f"Subscribers{f' - {tier_filter} Tier' if tier_filter else ''}",
                description=f"Page {i//subscribers_per_page + 1}/{(len(subscribers)-1)//subscribers_per_page + 1}",
                color=discord.Color.blue()
            )
            
            for sub in page_subscribers:
                # Format expiration date
                if sub["end_date"]:
                    end_date = datetime.fromisoformat(sub["end_date"])
                    expiry_text = end_date.strftime("%Y-%m-%d")
                    
                    # Check if expired
                    if end_date < datetime.now():
                        expiry_text += " (EXPIRED)"
                else:
                    expiry_text = "Never"
                
                embed.add_field(
                    name=f"{sub['username']} ({sub['user_id']})",
                    value=f"Tier: **{sub['tier']}**\nExpires: **{expiry_text}**\nActive: **{'Yes' if sub['active'] else 'No'}**",
                    inline=False
                )
            
            embeds.append(embed)
        
        # Send the first embed
        message = await ctx.send(embed=embeds[0])
        
        # If there's only one page, we're done
        if len(embeds) == 1:
            return
        
        # Add navigation reactions
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"] and reaction.message.id == message.id
        
        current_page = 0
        
        # Wait for reactions and change pages accordingly
        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                
                if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == "⬅️" and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])
                
                # Remove the user's reaction
                await message.remove_reaction(reaction.emoji, user)
            
            except Exception:
                break
    
    @commands.command(name="export_subscribers")
    async def export_subscribers(self, ctx, tier=None):
        """
        Export subscribers to a CSV file.
        
        Usage: !export_subscribers [tier]
        """
        if tier and tier.capitalize() not in config.SUBSCRIPTION_TIERS:
            await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
            return
        
        tier_filter = tier.capitalize() if tier else None
        subscribers = await database.get_all_subscribers(tier=tier_filter)
        
        if not subscribers:
            await ctx.send("No subscribers found." if not tier else f"No subscribers found for tier: {tier_filter}")
            return
        
        # Create CSV file in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "User ID", "Username", "Tier", "Start Date", "End Date", 
            "Active", "Transaction ID", "Payment Method"
        ])
        
        # Write data
        for sub in subscribers:
            writer.writerow([
                sub["user_id"],
                sub["username"],
                sub["tier"],
                sub["start_date"],
                sub["end_date"] or "Never",
                "Yes" if sub["active"] else "No",
                sub["transaction_id"] or "N/A",
                sub["payment_method"] or "N/A"
            ])
        
        # Reset the cursor to the beginning of the file
        output.seek(0)
        
        # Create a Discord file from the CSV
        file_name = f"subscribers{'_' + tier_filter if tier_filter else ''}.csv"
        file = discord.File(fp=io.BytesIO(output.getvalue().encode()), filename=file_name)
        
        await ctx.send(f"Here's the subscriber export for {tier_filter or 'all tiers'}:", file=file)
    
    @commands.command(name="subscription_report")
    async def subscription_report(self, ctx, days: int = 30):
        """
        Generate a subscription usage report.
        
        Usage: !subscription_report [days=30]
        """
        if days <= 0:
            await ctx.send("Days must be a positive number.")
            return
        
        # Get subscription metrics
        metrics = await database.get_subscription_metrics(days=days)
        
        # Create the report embed
        embed = discord.Embed(
            title=f"Subscription Report - Last {days} Days",
            color=discord.Color.blue()
        )
        
        # Add subscriber counts by tier
        tier_counts = metrics["subscribers_by_tier"]
        tier_text = "\n".join([f"**{tier}**: {count}" for tier, count in tier_counts.items()])
        
        embed.add_field(
            name="Current Subscribers",
            value=f"Total: **{metrics['total_subscribers']}**\n{tier_text}",
            inline=False
        )
        
        # Add subscription changes
        embed.add_field(
            name="Subscription Changes",
            value=(
                f"New Subscribers: **{metrics['new_subscribers']}**\n"
                f"Upgrades: **{metrics['upgrades']}**\n"
                f"Expirations: **{metrics['expirations']}**"
            ),
            inline=False
        )
        
        # Add timestamp
        embed.set_footer(text=f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="admin_upgrade")
    async def admin_upgrade(self, ctx, user_id: int, tier, duration_days: int = 30, *, reason=None):
        """
        Manually upgrade a user's subscription.
        
        Usage: !admin_upgrade <user_id> <tier> [duration_days=30] [reason]
        """
        # Validate tier
        if tier.capitalize() not in config.SUBSCRIPTION_TIERS:
            await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
            return
        
        tier = tier.capitalize()
        
        # Check if user exists
        user = await database.get_user(user_id)
        if not user:
            await ctx.send(f"User with ID {user_id} not found in the database.")
            return
        
        # Get current subscription
        current_subscription = await database.get_subscription(user_id)
        current_tier = current_subscription["tier"] if current_subscription else "None"
        
        # Update subscription
        success = await database.update_subscription(
            user_id, 
            tier, 
            duration_days=duration_days,
            admin_id=ctx.author.id,
            reason=reason or f"Admin upgrade by {ctx.author.name}"
        )
        
        if success:
            embed = discord.Embed(
                title="Subscription Updated",
                description=f"Successfully updated subscription for user ID: {user_id}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"User: **{user['username']}**\n"
                    f"Previous Tier: **{current_tier}**\n"
                    f"New Tier: **{tier}**\n"
                    f"Duration: **{duration_days}** days\n"
                    f"Reason: {reason or 'Admin action'}"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            logger.info(f"Admin {ctx.author.name} (ID: {ctx.author.id}) upgraded user {user['username']} (ID: {user_id}) from {current_tier} to {tier}")
        else:
            await ctx.send(f"Failed to update subscription for user ID: {user_id}")
    
    @commands.command(name="admin_extend")
    async def admin_extend(self, ctx, user_id: int, additional_days: int, *, reason=None):
        """
        Extend a user's subscription period.
        
        Usage: !admin_extend <user_id> <additional_days> [reason]
        """
        if additional_days <= 0:
            await ctx.send("Additional days must be a positive number.")
            return
        
        # Check if user exists
        user = await database.get_user(user_id)
        if not user:
            await ctx.send(f"User with ID {user_id} not found in the database.")
            return
        
        # Get current subscription
        subscription = await database.get_subscription(user_id)
        if not subscription:
            await ctx.send(f"User with ID {user_id} does not have an active subscription.")
            return
        
        if subscription["tier"] == "Basic":
            await ctx.send("Cannot extend Basic tier subscriptions as they don't expire.")
            return
        
        # Extend subscription
        success = await database.extend_subscription(
            user_id,
            additional_days,
            admin_id=ctx.author.id,
            reason=reason or f"Admin extension by {ctx.author.name}"
        )
        
        if success:
            # Calculate new end date
            current_end_date = datetime.fromisoformat(subscription["end_date"])
            new_end_date = current_end_date + timedelta(days=additional_days)
            
            embed = discord.Embed(
                title="Subscription Extended",
                description=f"Successfully extended subscription for user ID: {user_id}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Details",
                value=(
                    f"User: **{user['username']}**\n"
                    f"Tier: **{subscription['tier']}**\n"
                    f"Previous End Date: **{current_end_date.strftime('%Y-%m-%d')}**\n"
                    f"New End Date: **{new_end_date.strftime('%Y-%m-%d')}**\n"
                    f"Extended By: **{additional_days}** days\n"
                    f"Reason: {reason or 'Admin action'}"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
            logger.info(f"Admin {ctx.author.name} (ID: {ctx.author.id}) extended subscription for user {user['username']} (ID: {user_id}) by {additional_days} days")
        else:
            await ctx.send(f"Failed to extend subscription for user ID: {user_id}")
    
    @commands.command(name="view_subscription")
    async def view_subscription(self, ctx, user_id: int):
        """
        View detailed subscription information for a user.
        
        Usage: !view_subscription <user_id>
        """
        # Check if user exists
        user = await database.get_user(user_id)
        if not user:
            await ctx.send(f"User with ID {user_id} not found in the database.")
            return
        
        # Get current subscription
        subscription = await database.get_subscription(user_id)
        if not subscription:
            await ctx.send(f"User with ID {user_id} does not have an active subscription.")
            return
        
        # Get subscription history
        history = await database.get_subscription_history(user_id, limit=5)
        
        # Create the embed
        embed = discord.Embed(
            title=f"Subscription Details - {user['username']}",
            color=discord.Color.blue()
        )
        
        # Add current subscription details
        tier_details = config.SUBSCRIPTION_TIERS.get(subscription["tier"], {})
        
        embed.add_field(
            name="Current Subscription",
            value=(
                f"Tier: **{subscription['tier']}**\n"
                f"Start Date: **{subscription['start_date']}**\n"
                f"End Date: **{subscription['end_date'] or 'Never'}**\n"
                f"Active: **{'Yes' if subscription['active'] else 'No'}**\n"
                f"Transaction ID: **{subscription['transaction_id'] or 'N/A'}**\n"
                f"Payment Method: **{subscription['payment_method'] or 'N/A'}**"
            ),
            inline=False
        )
        
        # Add tier benefits
        if tier_details:
            embed.add_field(
                name="Tier Benefits",
                value="\n".join([f"• {feature}" for feature in tier_details.get("features", [])]),
                inline=False
            )
        
        # Add subscription history
        if history:
            history_text = ""
            for entry in history:
                admin_text = f" by Admin ID: {entry['admin_id']}" if entry['admin_id'] else ""
                reason_text = f"\n   Reason: {entry['reason']}" if entry['reason'] else ""
                history_text += f"• {entry['changed_at']}: **{entry['previous_tier']}** → **{entry['new_tier']}**{admin_text}{reason_text}\n"
            
            embed.add_field(
                name="Recent Subscription Changes",
                value=history_text,
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="subscription_history")
    async def subscription_history(self, ctx, user_id: int, limit: int = 10):
        """
        View detailed subscription history for a user.
        
        Usage: !subscription_history <user_id> [limit=10]
        """
        # Check if user exists
        user = await database.get_user(user_id)
        if not user:
            await ctx.send(f"User with ID {user_id} not found in the database.")
            return
        
        # Get subscription history
        history = await database.get_subscription_history(user_id, limit=limit)
        
        if not history:
            await ctx.send(f"No subscription history found for user ID: {user_id}")
            return
        
        # Create the embed
        embed = discord.Embed(
            title=f"Subscription History - {user['username']}",
            description=f"Showing up to {limit} most recent changes",
            color=discord.Color.blue()
        )
        
        # Add history entries
        for i, entry in enumerate(history):
            admin_text = f" by Admin ID: {entry['admin_id']}" if entry['admin_id'] else ""
            reason_text = f"\nReason: {entry['reason']}" if entry['reason'] else ""
            
            embed.add_field(
                name=f"{i+1}. {entry['changed_at']}",
                value=f"**{entry['previous_tier']}** → **{entry['new_tier']}**{admin_text}{reason_text}",
                inline=False
            )
        
        await ctx.send(embed=embed)

def setup(bot):
    """Add the admin subscription commands to the bot."""
    bot.add_cog(AdminSubscription(bot))
