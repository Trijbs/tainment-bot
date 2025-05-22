#!/usr/bin/env python3
"""
Tainment+ Discord Bot - Main Entry Point

This is the main file for the Tainment+ Discord bot, which handles the bot's
initialization, event handling, and command registration.

The bot provides entertainment features and a subscription-based model with
different tiers (Basic, Premium, Pro).
"""

import asyncio
import logging
import os
import sys
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
import database
import entertainment
import subscription
import utils
import leaderboard
import payment
import subscription_tasks
import admin_subscription

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tainment_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tainment_bot")

# Initialize the bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    """Event handler for when the bot is ready and connected to Discord."""
    logger.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guilds")
    
    # Initialize the database
    try:
        await database.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        traceback.print_exc()
        return
    
    # Set bot activity
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{config.COMMAND_PREFIX}help | Tainment+"
    )
    await bot.change_presence(activity=activity)
    
    logger.info("Bot is ready!")

@bot.event
async def on_guild_join(guild):
    """Event handler for when the bot joins a new guild."""
    logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
    
    # Send welcome message to the first available text channel
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            welcome_embed = discord.Embed(
                title="Thanks for adding Tainment+!",
                description=f"Use `{config.COMMAND_PREFIX}help` to see available commands.",
                color=discord.Color.blue()
            )
            welcome_embed.add_field(
                name="Subscription",
                value=f"Use `{config.COMMAND_PREFIX}subscribe` to view subscription options.",
                inline=False
            )
            await channel.send(embed=welcome_embed)
            break

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Command on cooldown. Try again in {error.retry_after:.2f} seconds.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        logger.error(f"Command error: {error}")
        traceback.print_exc()
        await ctx.send("An error occurred while executing the command.")

@bot.command(name="help")
async def help_command(ctx):
    """Display help information about the bot and its commands."""
    embed = discord.Embed(
        title="Tainment+ Help",
        description="Welcome to Tainment+! Here are the available commands:",
        color=discord.Color.blue()
    )
    
    # Entertainment commands
    embed.add_field(
        name="🎮 Entertainment",
        value=(
            f"`{config.COMMAND_PREFIX}joke` - Get a random joke\n"
            f"`{config.COMMAND_PREFIX}joke_categories` - List available joke categories\n"
            f"`{config.COMMAND_PREFIX}daily_joke` - Get the daily joke\n"
            f"`{config.COMMAND_PREFIX}story` - Get a short story\n"
            f"`{config.COMMAND_PREFIX}story_genres` - List available story genres\n"
            f"`{config.COMMAND_PREFIX}story_continue` - Read multi-part stories\n"
            f"`{config.COMMAND_PREFIX}game` - Play a simple game\n"
            f"`{config.COMMAND_PREFIX}leaderboard` - View game leaderboards"
        ),
        inline=False
    )
    
    # Subscription commands
    embed.add_field(
        name="💳 Subscription",
        value=(
            f"`{config.COMMAND_PREFIX}subscribe` - View subscription options\n"
            f"`{config.COMMAND_PREFIX}tier` - Check your subscription tier\n"
            f"`{config.COMMAND_PREFIX}upgrade` - Upgrade your subscription"
        ),
        inline=False
    )
    
    # Info commands
    embed.add_field(
        name="ℹ️ Information",
        value=(
            f"`{config.COMMAND_PREFIX}help` - Show this help message\n"
            f"`{config.COMMAND_PREFIX}tos` - View Terms of Service\n"
            f"`{config.COMMAND_PREFIX}privacy` - View Privacy Policy"
        ),
        inline=False
    )
    
    await ctx.send(embed=embed)

async def load_extensions():
    """Load all command extensions."""
    # Register entertainment commands
    entertainment.setup(bot)
    
    # Register leaderboard system
    leaderboard.setup(bot)
    
    # Register subscription commands
    subscription.setup(bot)
    
    # Register subscription tasks
    subscription_tasks.setup(bot)
    
    # Register admin subscription commands
    admin_subscription.setup(bot)
    
    # Register info commands
    bot.add_command(utils.tos)
    bot.add_command(utils.privacy)

async def main():
    """Main entry point for the bot."""
    # Load environment variables
    load_dotenv()
    
    # Load extensions
    await load_extensions()
    
    # Start the bot
    try:
        token = config.BOT_TOKEN
        if not token:
            logger.error("Bot token not found. Please set the BOT_TOKEN environment variable.")
            return
        
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token. Please check your token and try again.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
