
"""
Tainment+ Discord Bot - Utility Functions

This module contains utility functions and commands for the Tainment+ Discord bot,
including access to Terms of Service and Privacy Policy.
"""

import discord
import logging
import os
from discord.ext import commands

import config

logger = logging.getLogger("tainment_bot.utils")

@commands.command(name="tos")
async def tos(ctx):
    """Display the Terms of Service."""
    try:
        # Check if the file exists
        if not os.path.exists(config.TOS_PATH):
            await ctx.send("Terms of Service document not found. Please contact the administrator.")
            return
        
        # Read the Terms of Service file
        with open(config.TOS_PATH, 'r') as file:
            content = file.read()
        
        # Create an embed for the ToS
        embed = discord.Embed(
            title="Tainment+ Terms of Service",
            description="By using Tainment+, you agree to the following terms:",
            color=discord.Color.blue()
        )
        
        # Split content if it's too long for a single embed
        if len(content) > 4000:
            # Send the first part in the embed
            embed.add_field(
                name="Terms of Service (Summary)",
                value=content[:4000] + "...",
                inline=False
            )
            await ctx.send(embed=embed)
            
            # Send the full document as a file
            await ctx.send("Here's the complete Terms of Service document:", 
                          file=discord.File(config.TOS_PATH))
        else:
            # If content fits in a single embed
            embed.add_field(
                name="Terms of Service",
                value=content,
                inline=False
            )
            await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Error displaying Terms of Service: {e}")
        await ctx.send("An error occurred while retrieving the Terms of Service. Please try again later.")

@commands.command(name="privacy")
async def privacy(ctx):
    """Display the Privacy Policy."""
    try:
        # Check if the file exists
        if not os.path.exists(config.PRIVACY_PATH):
            await ctx.send("Privacy Policy document not found. Please contact the administrator.")
            return
        
        # Read the Privacy Policy file
        with open(config.PRIVACY_PATH, 'r') as file:
            content = file.read()
        
        # Create an embed for the Privacy Policy
        embed = discord.Embed(
            title="Tainment+ Privacy Policy",
            description="Tainment+ is committed to protecting your privacy:",
            color=discord.Color.blue()
        )
        
        # Split content if it's too long for a single embed
        if len(content) > 4000:
            # Send the first part in the embed
            embed.add_field(
                name="Privacy Policy (Summary)",
                value=content[:4000] + "...",
                inline=False
            )
            await ctx.send(embed=embed)
            
            # Send the full document as a file
            await ctx.send("Here's the complete Privacy Policy document:", 
                          file=discord.File(config.PRIVACY_PATH))
        else:
            # If content fits in a single embed
            embed.add_field(
                name="Privacy Policy",
                value=content,
                inline=False
            )
            await ctx.send(embed=embed)
    
    except Exception as e:
        logger.error(f"Error displaying Privacy Policy: {e}")
        await ctx.send("An error occurred while retrieving the Privacy Policy. Please try again later.")

def format_time(seconds):
    """Format seconds into a human-readable time string."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    time_parts = []
    if days > 0:
        time_parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not time_parts:
        time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    return ", ".join(time_parts)

def create_progress_bar(current, total, length=10):
    """Create a text-based progress bar."""
    filled_length = int(length * current / total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    percent = int(100 * current / total)
    return f"{bar} {percent}%"

def truncate_text(text, max_length=2000):
    """Truncate text to a maximum length, adding an ellipsis if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
