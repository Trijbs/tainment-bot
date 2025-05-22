
"""
Tainment+ Discord Bot - Configuration

This module contains configuration settings for the Tainment+ Discord bot.
It loads environment variables and provides default values for various settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token (required for the bot to connect to Discord)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Command prefix (what users type before commands)
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "t!")

# Database settings
DB_PATH = os.getenv("DB_PATH", "tainment.db")

# Subscription tiers and pricing
SUBSCRIPTION_TIERS = {
    "Basic": {
        "price": 0,
        "description": "Basic access to entertainment features",
        "features": ["Random jokes", "Basic stories"]
    },
    "Premium": {
        "price": 4.99,
        "description": "Enhanced entertainment features",
        "features": ["Premium jokes", "Advanced stories", "Simple games"]
    },
    "Pro": {
        "price": 9.99,
        "description": "Full access to all entertainment features",
        "features": ["All Premium features", "Exclusive content", "Advanced games"]
    }
}

# Cooldown settings (in seconds)
COOLDOWNS = {
    "joke": 5,
    "story": 10,
    "game": 30
}

# Paths to legal documents
TOS_PATH = os.path.expanduser("~/Tainment_Terms_of_Service.md")
PRIVACY_PATH = os.path.expanduser("~/Tainment_Privacy_Policy.md")

# Colors for embeds
COLORS = {
    "primary": 0x3498db,  # Blue
    "success": 0x2ecc71,  # Green
    "warning": 0xf1c40f,  # Yellow
    "error": 0xe74c3c,    # Red
    "info": 0x9b59b6      # Purple
}
