"""
Tainment+ Discord Bot - Subscription Management

This module handles subscription-related commands and functionality for the
Tainment+ Discord bot, including subscription management and tier upgrades.
"""

import discord
import logging
from discord.ext import commands
from datetime import datetime, timedelta

import config
import database
import payment

logger = logging.getLogger("tainment_bot.subscription")

@commands.command(name="subscribe")
async def subscribe(ctx):
    """View available subscription options."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    current_tier = subscription["tier"] if subscription else "None"
    
    # Create embed with subscription options
    embed = discord.Embed(
        title="Tainment+ Subscription Options",
        description="Choose the subscription tier that's right for you!",
        color=discord.Color.blue()
    )
    
    # Add field for each tier
    for tier, details in config.SUBSCRIPTION_TIERS.items():
        features_list = "\n".join([f"• {feature}" for feature in details["features"]])
        price_text = "Free" if details["price"] == 0 else f"${details['price']:.2f}/month"
        
        # Highlight current tier
        if tier == current_tier:
            embed.add_field(
                name=f"✅ {tier} - {price_text}",
                value=f"**{details['description']}**\n{features_list}\n**Your current tier**",
                inline=False
            )
        else:
            embed.add_field(
                name=f"{tier} - {price_text}",
                value=f"{details['description']}\n{features_list}",
                inline=False
            )
    
    # Add upgrade instructions
    embed.add_field(
        name="How to Upgrade",
        value=f"Use `{ctx.prefix}upgrade <tier>` to upgrade your subscription.",
        inline=False
    )
    
    # Add footer with terms link
    embed.set_footer(text=f"By subscribing, you agree to our Terms of Service. Use {ctx.prefix}tos to view.")
    
    await ctx.send(embed=embed)

@commands.command(name="tier")
async def tier(ctx):
    """Check your current subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    
    if not subscription:
        await ctx.send(f"You don't have an active subscription. Use `{ctx.prefix}subscribe` to view options.")
        return
    
    tier_name = subscription["tier"]
    tier_details = config.SUBSCRIPTION_TIERS.get(tier_name, {})
    
    # Create embed with subscription details
    embed = discord.Embed(
        title="Your Tainment+ Subscription",
        description=f"You are currently subscribed to the **{tier_name}** tier.",
        color=discord.Color.green()
    )
    
    # Add tier details
    if tier_details:
        embed.add_field(
            name="Tier Benefits",
            value="\n".join([f"• {feature}" for feature in tier_details.get("features", [])]),
            inline=False
        )
    
    # Add subscription dates if applicable
    if subscription["end_date"] and tier_name != "Basic":
        end_date = datetime.fromisoformat(subscription["end_date"])
        start_date = datetime.fromisoformat(subscription["start_date"])
        
        # Check if subscription is expired or in grace period
        if end_date < datetime.now():
            if subscription.get("grace_period_end") and datetime.fromisoformat(subscription["grace_period_end"]) > datetime.now():
                grace_end = datetime.fromisoformat(subscription["grace_period_end"])
                hours_left = int((grace_end - datetime.now()).total_seconds() / 3600)
                
                embed.add_field(
                    name="⚠️ Subscription Expired - Grace Period Active",
                    value=f"Your subscription expired on {end_date.strftime('%Y-%m-%d')}.\nGrace period ends in **{hours_left}** hours.\nPlease renew to avoid losing premium features.",
                    inline=False
                )
                embed.color = discord.Color.gold()
            else:
                embed.add_field(
                    name="❌ Subscription Expired",
                    value=f"Your subscription expired on {end_date.strftime('%Y-%m-%d')}.\nRenew now to regain premium features!",
                    inline=False
                )
                embed.color = discord.Color.red()
        else:
            days_left = (end_date - datetime.now()).days + 1
            embed.add_field(
                name="Subscription Period",
                value=f"Started: {start_date.strftime('%Y-%m-%d')}\nExpires: {end_date.strftime('%Y-%m-%d')} ({days_left} days left)",
                inline=False
            )
    
    # Add upgrade/renew instructions
    if tier_name != "Pro":
        embed.add_field(
            name="Upgrade Your Experience",
            value=f"Use `{ctx.prefix}upgrade <tier>` to upgrade your subscription.",
            inline=False
        )
    elif subscription["end_date"] and datetime.fromisoformat(subscription["end_date"]) < datetime.now() + timedelta(days=7):
        embed.add_field(
            name="Renew Your Subscription",
            value=f"Use `{ctx.prefix}renew` to renew your subscription.",
            inline=False
        )
    
    # Add payment history if available
    payment_history = await database.get_user_payment_history(user_id, limit=1)
    if payment_history:
        latest_payment = payment_history[0]
        embed.add_field(
            name="Latest Payment",
            value=f"Amount: ${latest_payment['amount']:.2f}\nDate: {datetime.fromisoformat(latest_payment['created_at']).strftime('%Y-%m-%d')}\nTransaction ID: {latest_payment['transaction_id']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@commands.command(name="upgrade")
async def upgrade(ctx, tier=None):
    """Upgrade your subscription to a higher tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    current_tier = subscription["tier"] if subscription else "Basic"
    
    # Check if tier is provided
    if not tier:
        await ctx.send(f"Please specify a tier to upgrade to. Use `{ctx.prefix}subscribe` to see available tiers.")
        return
    
    # Validate tier
    tier = tier.capitalize()
    if tier not in config.SUBSCRIPTION_TIERS:
        await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
        return
    
    # Check if already subscribed to this tier
    if tier == current_tier:
        await ctx.send(f"You are already subscribed to the {tier} tier.")
        return
    
    # Check if downgrading (not allowed through this command)
    tier_levels = {"Basic": 0, "Premium": 1, "Pro": 2}
    if tier_levels.get(tier, 0) < tier_levels.get(current_tier, 0):
        await ctx.send("Downgrading is not supported. Please contact support for assistance.")
        return
    
    # Create checkout view for payment processing
    checkout_view = payment.CheckoutView(user_id, username, tier)
    
    # Create initial checkout embed
    price = config.SUBSCRIPTION_TIERS[tier]["price"]
    embed = discord.Embed(
        title="Subscription Upgrade",
        description=f"You are about to upgrade from **{current_tier}** to **{tier}**.",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Price",
        value=f"${price:.2f}/month",
        inline=True
    )
    
    embed.add_field(
        name="Benefits",
        value="\n".join([f"• {feature}" for feature in config.SUBSCRIPTION_TIERS[tier]["features"]]),
        inline=False
    )
    
    embed.set_footer(text="Click 'Proceed to Payment' to continue with your upgrade.")
    
    # Send the checkout view
    checkout_view.message = await ctx.send(embed=embed, view=checkout_view)

@commands.command(name="subscription_benefits")
async def subscription_benefits(ctx, tier=None):
    """View detailed benefits of a specific tier or compare all tiers."""
    # If no tier specified, show comparison of all tiers
    if not tier:
        embed = discord.Embed(
            title="Tainment+ Subscription Tiers Comparison",
            description="Compare the benefits of each subscription tier",
            color=discord.Color.blue()
        )
        
        # Create a comparison table
        features_set = set()
        for tier_details in config.SUBSCRIPTION_TIERS.values():
            features_set.update(tier_details.get("features", []))
        
        # Sort features for consistent display
        all_features = sorted(list(features_set))
        
        # Add each feature as a field with tier availability
        for feature in all_features:
            value = ""
            for tier_name, tier_details in config.SUBSCRIPTION_TIERS.items():
                if feature in tier_details.get("features", []):
                    value += f"**{tier_name}**: ✅\n"
                else:
                    value += f"**{tier_name}**: ❌\n"
            
            embed.add_field(
                name=feature,
                value=value,
                inline=True
            )
        
        # Add pricing information
        pricing_info = "\n".join([
            f"**{tier_name}**: ${details['price']:.2f}/month" 
            for tier_name, details in config.SUBSCRIPTION_TIERS.items()
        ])
        
        embed.add_field(
            name="Pricing",
            value=pricing_info,
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    # Show detailed benefits for a specific tier
    tier = tier.capitalize()
    if tier not in config.SUBSCRIPTION_TIERS:
        await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
        return
    
    tier_details = config.SUBSCRIPTION_TIERS[tier]
    
    embed = discord.Embed(
        title=f"Tainment+ {tier} Tier Benefits",
        description=tier_details["description"],
        color=discord.Color.blue()
    )
    
    # Add price
    embed.add_field(
        name="Price",
        value=f"${tier_details['price']:.2f}/month",
        inline=False
    )
    
    # Add features with detailed descriptions
    features = tier_details.get("features", [])
    
    # Here we would ideally have more detailed descriptions for each feature
    # For this example, we'll just list them with bullet points
    features_text = "\n".join([f"• {feature}" for feature in features])
    
    embed.add_field(
        name="Features",
        value=features_text or "No features available",
        inline=False
    )
    
    # Add upgrade instructions if not viewing the highest tier
    if tier != "Pro":
        next_tier = "Premium" if tier == "Basic" else "Pro"
        embed.add_field(
            name="Upgrade Path",
            value=f"Upgrade to **{next_tier}** tier for even more features!\nUse `{ctx.prefix}upgrade {next_tier}` to upgrade.",
            inline=False
        )
    
    await ctx.send(embed=embed)

@commands.command(name="simulate_upgrade")
async def simulate_upgrade(ctx, tier=None):
    """Simulate upgrading to a different tier to see the benefits and cost."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    current_tier = subscription["tier"] if subscription else "Basic"
    
    # Check if tier is provided
    if not tier:
        await ctx.send(f"Please specify a tier to simulate upgrading to. Use `{ctx.prefix}subscribe` to see available tiers.")
        return
    
    # Validate tier
    tier = tier.capitalize()
    if tier not in config.SUBSCRIPTION_TIERS:
        await ctx.send(f"Invalid tier. Available tiers: {', '.join(config.SUBSCRIPTION_TIERS.keys())}")
        return
    
    # Check if already subscribed to this tier
    if tier == current_tier:
        await ctx.send(f"You are already subscribed to the {tier} tier.")
        return
    
    # Check if downgrading (show different message)
    tier_levels = {"Basic": 0, "Premium": 1, "Pro": 2}
    is_downgrade = tier_levels.get(tier, 0) < tier_levels.get(current_tier, 0)
    
    # Create simulation embed
    embed = discord.Embed(
        title="Subscription Change Simulation",
        description=f"This is a simulation of {'downgrading' if is_downgrade else 'upgrading'} from **{current_tier}** to **{tier}**.",
        color=discord.Color.gold()
    )
    
    # Add current tier benefits
    current_tier_details = config.SUBSCRIPTION_TIERS.get(current_tier, {})
    current_features = current_tier_details.get("features", [])
    
    embed.add_field(
        name=f"Your Current Tier: {current_tier}",
        value="\n".join([f"• {feature}" for feature in current_features]) or "No features",
        inline=False
    )
    
    # Add new tier benefits
    new_tier_details = config.SUBSCRIPTION_TIERS.get(tier, {})
    new_features = new_tier_details.get("features", [])
    
    embed.add_field(
        name=f"Simulated Tier: {tier}",
        value="\n".join([f"• {feature}" for feature in new_features]) or "No features",
        inline=False
    )
    
    # Calculate price difference
    current_price = current_tier_details.get("price", 0)
    new_price = new_tier_details.get("price", 0)
    price_difference = new_price - current_price
    
    if price_difference > 0:
        price_text = f"You would pay ${price_difference:.2f}/month more"
    elif price_difference < 0:
        price_text = f"You would save ${abs(price_difference):.2f}/month"
    else:
        price_text = "There would be no price change"
    
    embed.add_field(
        name="Price Impact",
        value=f"Current: ${current_price:.2f}/month\nNew: ${new_price:.2f}/month\n{price_text}",
        inline=False
    )
    
    # Add feature comparison
    gained_features = [f for f in new_features if f not in current_features]
    lost_features = [f for f in current_features if f not in new_features]
    
    if gained_features:
        embed.add_field(
            name="Features You Would Gain",
            value="\n".join([f"• {feature}" for feature in gained_features]),
            inline=False
        )
    
    if lost_features:
        embed.add_field(
            name="Features You Would Lose",
            value="\n".join([f"• {feature}" for feature in lost_features]),
            inline=False
        )
    
    # Add action buttons
    embed.add_field(
        name="Ready to Change?",
        value=f"Use `{ctx.prefix}upgrade {tier}` to upgrade to this tier." if not is_downgrade else "Downgrading requires contacting support.",
        inline=False
    )
    
    await ctx.send(embed=embed)

@commands.command(name="subscription_status")
async def subscription_status(ctx):
    """Check your subscription status and expiration date."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    
    if not subscription:
        await ctx.send(f"You don't have an active subscription. Use `{ctx.prefix}subscribe` to view options.")
        return
    
    tier_name = subscription["tier"]
    
    # Create embed with subscription status
    embed = discord.Embed(
        title="Subscription Status",
        color=discord.Color.blue()
    )
    
    # Add basic subscription info
    embed.add_field(
        name="Current Tier",
        value=f"**{tier_name}**",
        inline=True
    )
    
    embed.add_field(
        name="Status",
        value="**Active**" if subscription["active"] else "**Inactive**",
        inline=True
    )
    
    # Add dates
    start_date = datetime.fromisoformat(subscription["start_date"])
    embed.add_field(
        name="Start Date",
        value=start_date.strftime("%Y-%m-%d"),
        inline=True
    )
    
    # Add expiration info if applicable
    if subscription["end_date"] and tier_name != "Basic":
        end_date = datetime.fromisoformat(subscription["end_date"])
        days_left = (end_date - datetime.now()).days
        
        status_color = discord.Color.green()
        status_text = "Active"
        
        if days_left < 0:
            # Check if in grace period
            if subscription.get("grace_period_end"):
                grace_end = datetime.fromisoformat(subscription["grace_period_end"])
                if grace_end > datetime.now():
                    hours_left = int((grace_end - datetime.now()).total_seconds() / 3600)
                    status_text = f"Grace Period ({hours_left} hours left)"
                    status_color = discord.Color.gold()
                else:
                    status_text = "Expired"
                    status_color = discord.Color.red()
            else:
                status_text = "Expired"
                status_color = discord.Color.red()
        elif days_left < 7:
            status_text = f"Expiring Soon ({days_left} days left)"
            status_color = discord.Color.gold()
        else:
            status_text = f"Active ({days_left} days left)"
        
        embed.color = status_color
        
        embed.add_field(
            name="End Date",
            value=end_date.strftime("%Y-%m-%d"),
            inline=True
        )
        
        embed.add_field(
            name="Status",
            value=f"**{status_text}**",
            inline=True
        )
        
        # Add renewal info
        if days_left < 7 and days_left >= 0:
            embed.add_field(
                name="Renewal",
                value=f"Your subscription will expire soon. Use `{ctx.prefix}renew` to renew your subscription.",
                inline=False
            )
        elif days_left < 0:
            embed.add_field(
                name="Renewal",
                value=f"Your subscription has expired. Use `{ctx.prefix}renew` to renew your subscription.",
                inline=False
            )
    else:
        embed.add_field(
            name="Expiration",
            value="Never (Basic tier doesn't expire)",
            inline=True
        )
    
    # Add payment info if available
    if subscription.get("transaction_id"):
        embed.add_field(
            name="Payment Information",
            value=f"Transaction ID: {subscription['transaction_id']}\nMethod: {subscription.get('payment_method', 'N/A')}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@commands.command(name="renew")
async def renew(ctx, duration_months: int = 1):
    """Renew your current subscription."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get current subscription
    subscription = await database.get_subscription(user_id)
    
    if not subscription:
        await ctx.send(f"You don't have an active subscription to renew. Use `{ctx.prefix}subscribe` to view options.")
        return
    
    current_tier = subscription["tier"]
    
    # Basic tier doesn't need renewal
    if current_tier == "Basic":
        await ctx.send("The Basic tier doesn't require renewal as it never expires.")
        return
    
    # Validate duration
    if duration_months not in [1, 3, 6, 12]:
        await ctx.send("Please choose a valid duration: 1, 3, 6, or 12 months.")
        return
    
    # Create checkout view for payment processing
    checkout_view = payment.CheckoutView(user_id, username, current_tier, duration_months)
    
    # Calculate price with potential discount
    base_price = config.SUBSCRIPTION_TIERS[current_tier]["price"]
    total_price = await payment.calculate_price(current_tier, duration_months)
    
    # Create initial checkout embed
    embed = discord.Embed(
        title="Subscription Renewal",
        description=f"You are about to renew your **{current_tier}** subscription for **{duration_months}** month{'s' if duration_months > 1 else ''}.",
        color=discord.Color.gold()
    )
    
    # Add pricing details
    if duration_months > 1:
        discount_percent = round((1 - (total_price / (base_price * duration_months))) * 100)
        embed.add_field(
            name="Price",
            value=f"${base_price:.2f}/month × {duration_months} months = ${base_price * duration_months:.2f}\nWith {discount_percent}% discount: **${total_price:.2f}**",
            inline=False
        )
    else:
        embed.add_field(
            name="Price",
            value=f"**${total_price:.2f}** for 1 month",
            inline=False
        )
    
    # Add benefits reminder
    tier_details = config.SUBSCRIPTION_TIERS.get(current_tier, {})
    features = tier_details.get("features", [])
    
    embed.add_field(
        name="Benefits You'll Continue to Enjoy",
        value="\n".join([f"• {feature}" for feature in features]) or "No features available",
        inline=False
    )
    
    embed.set_footer(text="Click 'Proceed to Payment' to continue with your renewal.")
    
    # Send the checkout view
    checkout_view.message = await ctx.send(embed=embed, view=checkout_view)

@commands.command(name="payment_history")
async def payment_history(ctx, limit: int = 5):
    """View your payment history."""
    user_id = ctx.author.id
    
    # Get payment history
    payment_history = await database.get_user_payment_history(user_id, limit=limit)
    
    if not payment_history:
        await ctx.send("You don't have any payment history.")
        return
    
    # Create embed
    embed = discord.Embed(
        title="Your Payment History",
        description=f"Showing your {len(payment_history)} most recent payments",
        color=discord.Color.blue()
    )
    
    # Add each payment as a field
    for i, payment in enumerate(payment_history):
        created_at = datetime.fromisoformat(payment["created_at"])
        completed_at = datetime.fromisoformat(payment["completed_at"]) if payment["completed_at"] else None
        
        embed.add_field(
            name=f"Payment {i+1} - {created_at.strftime('%Y-%m-%d')}",
            value=(
                f"Amount: **${payment['amount']:.2f}**\n"
                f"Tier: **{payment['tier']}**\n"
                f"Duration: **{payment['duration_days']}** days\n"
                f"Status: **{payment['status'].capitalize()}**\n"
                f"Transaction ID: `{payment['transaction_id']}`\n"
                f"Completed: {completed_at.strftime('%Y-%m-%d %H:%M') if completed_at else 'N/A'}"
            ),
            inline=False
        )
    
    await ctx.send(embed=embed)

def setup(bot):
    """Add all subscription commands to the bot."""
    bot.add_command(subscribe)
    bot.add_command(tier)
    bot.add_command(upgrade)
    bot.add_command(subscription_benefits)
    bot.add_command(simulate_upgrade)
    bot.add_command(subscription_status)
    bot.add_command(renew)
    bot.add_command(payment_history)
