# Tainment+ Discord Bot

Tainment+ is a Discord bot that provides entertainment features and a subscription-based model with different tiers.

## Features

- **Entertainment Features**
  - Jokes: Get random jokes based on your subscription tier
  - Stories: Read short stories based on your subscription tier
  - Games: Play simple games (Premium and Pro tiers only)

- **Subscription Model**
  - Basic Tier (Free): Access to basic jokes and stories
  - Premium Tier ($4.99/month): Access to premium jokes, advanced stories, and simple games
  - Pro Tier ($9.99/month): Full access to all entertainment features, including exclusive content and advanced games

- **Enhanced Subscription Management**
  - Detailed subscription status and expiration tracking
  - Grace period for expired subscriptions
  - Renewal notifications before expiration
  - Payment processing simulation
  - Subscription history tracking
  - Admin tools for subscription management

## Commands

### Entertainment Commands
- `t!joke` - Get a random joke
- `t!joke_categories` - List available joke categories
- `t!daily_joke` - Get the daily joke
- `t!story` - Get a short story
- `t!story_genres` - List available story genres
- `t!story_continue` - Read multi-part stories
- `t!game` - Play a simple game
- `t!leaderboard` - View game leaderboards

### Subscription Commands
- `t!subscribe` - View subscription options
- `t!tier` - Check your current subscription tier
- `t!upgrade <tier>` - Upgrade your subscription to a higher tier
- `t!subscription_benefits [tier]` - View detailed benefits of each tier
- `t!simulate_upgrade <tier>` - Simulate upgrading to a different tier
- `t!subscription_status` - Check subscription status and expiration date
- `t!renew [duration_months]` - Renew your current subscription
- `t!payment_history [limit]` - View your payment history

### Admin Subscription Commands
- `t!subscribers [tier]` - List all subscribers
- `t!export_subscribers [tier]` - Export subscribers to a CSV file
- `t!subscription_report [days]` - Generate a subscription usage report
- `t!admin_upgrade <user_id> <tier> [duration_days] [reason]` - Manually upgrade a user
- `t!admin_extend <user_id> <additional_days> [reason]` - Extend a user's subscription
- `t!view_subscription <user_id>` - View detailed subscription information for a user
- `t!subscription_history <user_id> [limit]` - View subscription history for a user

### Information Commands
- `t!help` - Display help information
- `t!tos` - View Terms of Service
- `t!privacy` - View Privacy Policy

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the following variables:
   ```
   BOT_TOKEN=your_discord_bot_token
   COMMAND_PREFIX=t!
   ```
4. Run the bot: `python main.py`

## Project Structure

```
tainment_bot/
  ├── main.py (main bot file)
  ├── config.py (configuration settings)
  ├── database.py (database operations)
  ├── entertainment.py (entertainment features)
  ├── subscription.py (subscription commands)
  ├── payment.py (payment processing)
  ├── subscription_tasks.py (subscription expiration checking)
  ├── admin_subscription.py (admin subscription commands)
  ├── utils.py (utility functions)
  ├── leaderboard.py (game leaderboards)
  └── README.md (documentation)
```

## Subscription System Features

### User-Facing Features
- **Detailed Subscription Information**: View subscription details with nicely formatted embeds
- **Tier Comparison**: Compare benefits across different subscription tiers
- **Upgrade Simulation**: Simulate upgrading to see the benefits and cost differences
- **Subscription Status**: Check subscription status and expiration date
- **Renewal System**: Renew subscriptions with flexible duration options
- **Payment Processing**: Simulated checkout process with confirmation steps

### Admin Features
- **Subscriber Management**: View all subscribers, filter by tier, export to CSV
- **Manual Subscription Control**: Upgrade/downgrade users, extend subscription periods
- **Reporting**: Generate subscription usage reports
- **User History**: View detailed subscription history for any user

### Background Tasks
- **Expiration Checking**: Automatically check for expiring subscriptions
- **Renewal Notifications**: Send DM notifications to users before subscription expiration
- **Grace Period**: Provide a grace period for expired subscriptions before downgrading

## Requirements

- Python 3.8+
- discord.py
- aiosqlite
- python-dotenv

## License

This project is licensed under the MIT License - see the LICENSE file for details.
