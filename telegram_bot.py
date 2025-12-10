#!/usr/bin/env python3
"""
Ryanair Flight Price Telegram Bot
Monitors flights between Fez (FEZ) and Agadir (AGA)
With price alerts functionality
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from ryanair_api import RyanairAPI

# Load environment variables
load_dotenv()

# Configuration - Fixed routes
ORIGIN = "AGA"  # Agadir, Morocco
DESTINATION = "FEZ"  # Fez, Morocco

# Get bot token from environment
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Price alerts storage file
ALERTS_FILE = "price_alerts.json"

# Store for price alerts: {chat_id: {"target_price": float, "active": bool}}
price_alerts = {}


def load_alerts():
    """Load price alerts from file"""
    global price_alerts
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, 'r') as f:
                price_alerts = json.load(f)
    except Exception as e:
        print(f"Error loading alerts: {e}")
        price_alerts = {}


def save_alerts():
    """Save price alerts to file"""
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(price_alerts, f)
    except Exception as e:
        print(f"Error saving alerts: {e}")


def get_current_lowest_price() -> tuple:
    """Get the current lowest price and details"""
    api = RyanairAPI()
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        results = api.get_cheapest_fares(
            origin=ORIGIN,
            destination=DESTINATION,
            date_out=start_date,
            flex_days=30,
        )
        
        outbound = results.get("outbound") or {}
        fares = outbound.get("fares", [])
        
        if not fares:
            return None, None, None
        
        # Find lowest price (exclude unavailable flights)
        lowest_price = float('inf')
        lowest_date = None
        currency = "MAD"
        
        for fare in fares:
            if not fare or fare.get("unavailable"):
                continue
            price = fare.get("price") or {}
            value = price.get("value")
            if value and value < lowest_price:
                lowest_price = value
                lowest_date = fare.get("day", "")
                currency = price.get("currencyCode", "MAD")
        
        if lowest_price == float('inf'):
            return None, None, None
            
        return lowest_price, lowest_date, currency
        
    except Exception as e:
        print(f"Error getting price: {e}")
        return None, None, None


def get_flight_prices_formatted(days: int = 30) -> str:
    """Get formatted flight prices"""
    api = RyanairAPI()
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        results = api.get_cheapest_fares(
            origin=ORIGIN,
            destination=DESTINATION,
            date_out=start_date,
            flex_days=days,
        )
        
        outbound = results.get("outbound") or {}
        fares = outbound.get("fares", [])
        
        if not fares:
            return "❌ No flights found for this route"
        
        # Collect valid fares (exclude unavailable)
        valid_fares = []
        for fare in fares:
            if not fare or fare.get("unavailable"):
                continue
            price = fare.get("price") or {}
            if price.get("value"):
                dep_time = fare.get("departureDate", "")
                arr_time = fare.get("arrivalDate", "")
                valid_fares.append({
                    "date": fare.get("day", ""),
                    "price": price.get("value"),
                    "currency": price.get("currencyCode", "MAD"),
                    "departure": dep_time[11:16] if dep_time else "",
                    "arrival": arr_time[11:16] if arr_time else "",
                })
        
        if not valid_fares:
            return "❌ No fares available for this route"
        
        # Sort by price
        valid_fares.sort(key=lambda x: x["price"])
        
        # Format output
        output = []
        output.append("╔══════════════════════════════╗")
        output.append("    ✈️ *AGADIR → FEZ* ✈️")
        output.append("╚══════════════════════════════╝")
        output.append("")
        
        # Show lowest price prominently
        lowest = valid_fares[0]
        lowest_day = datetime.strptime(lowest['date'], '%Y-%m-%d').strftime('%a')
        output.append(f"🏆 *BEST PRICE:* `{lowest['price']:.2f} {lowest['currency']}`")
        output.append(f"📅 {lowest['date']} ({lowest_day})")
        if lowest['departure']:
            output.append(f"🕐 {lowest['departure']} → {lowest['arrival']}")
        output.append("")
        output.append("┌─────────────────────────────┐")
        output.append("│    📊 *ALL FLIGHTS*         │")
        output.append("└─────────────────────────────┘")
        output.append("")
        
        # Sort by date for display
        by_date = sorted(valid_fares[:15], key=lambda x: x['date'])
        for fare in by_date:
            price_emoji = "🟢" if fare["price"] == lowest["price"] else "⚪"
            day_name = datetime.strptime(fare['date'], '%Y-%m-%d').strftime('%a')
            time_str = f"{fare['departure']}" if fare['departure'] else ""
            output.append(f"{price_emoji} `{fare['date']}` {day_name} {time_str} │ *{fare['price']:.0f} {fare['currency']}*")
        
        if len(valid_fares) > 15:
            output.append(f"\n_+{len(valid_fares) - 15} more dates available_")
        
        output.append("")
        output.append("🟢 = Lowest price")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error fetching flights: {str(e)}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with available commands"""
    
    # Get current lowest price
    lowest_price, lowest_date, currency = get_current_lowest_price()
    
    if lowest_price:
        day_name = datetime.strptime(lowest_date, '%Y-%m-%d').strftime('%A')
        price_info = f"💰 *Current lowest:* `{lowest_price:.2f} {currency}`\n📅 {lowest_date} ({day_name})"
    else:
        price_info = "💰 Checking prices..."
    
    welcome_message = f"""
╔══════════════════════════════╗
       ✈️  *RYANAIR FLIGHTS*  ✈️
╚══════════════════════════════╝

🛫 *Agadir* (AGA)  ──────►  *Fez* (FEZ) 🛬

{price_info}

┌─────────────────────────────┐
│       📋 *COMMANDS*         │
├─────────────────────────────┤
│ /prices  → All prices       │
│ /lowest  → Best deal        │
│ /alert   → Price alert      │
│ /myalert → Check alert      │
│ /help    → This menu        │
└─────────────────────────────┘

🕐 *Schedule:* Sat & Tue flights
⏱️ *Duration:* ~1h 20min
"""
    
    keyboard = [
        [InlineKeyboardButton("✈️ Check All Prices", callback_data="check_prices")],
        [InlineKeyboardButton("🏆 Lowest Price", callback_data="lowest_price")],
        [InlineKeyboardButton("🔔 Alert 150 MAD", callback_data="alert_150"),
         InlineKeyboardButton("🔔 Alert 200 MAD", callback_data="alert_200")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message"""
    await start(update, context)


async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get all prices for the next 30 days"""
    await update.message.reply_text("🔍 Fetching prices... please wait...")
    
    result = get_flight_prices_formatted(30)
    await update.message.reply_text(result, parse_mode="Markdown")


async def lowest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the current lowest price"""
    await update.message.reply_text("🔍 Finding lowest price...")
    
    lowest_price, lowest_date, currency = get_current_lowest_price()
    
    if lowest_price:
        day_name = datetime.strptime(lowest_date, '%Y-%m-%d').strftime('%A')
        message = f"""
╔══════════════════════════════╗
     🏆 *BEST DEAL FOUND!* 🏆
╚══════════════════════════════╝

🛫 *Agadir* → *Fez*

┌─────────────────────────────┐
│  💰 *{lowest_price:.2f} {currency}*
│  📅 {lowest_date}
│  📆 {day_name}
└─────────────────────────────┘

💡 _Set alert with:_ `/alert {int(lowest_price - 10)}`
"""
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Could not fetch price information")


async def set_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a price alert"""
    chat_id = str(update.effective_chat.id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify a target price\n"
            "Example: `/alert 25` (alert when price ≤ €25)",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_price = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid price. Please enter a number\n"
            "Example: `/alert 25`",
            parse_mode="Markdown"
        )
        return
    
    # Save the alert
    price_alerts[chat_id] = {
        "target_price": target_price,
        "active": True,
        "created": datetime.now().isoformat()
    }
    save_alerts()
    
    # Get current price for comparison
    lowest_price, lowest_date, currency = get_current_lowest_price()
    
    message = f"""
╔══════════════════════════════╗
     ✅ *ALERT ACTIVATED!* ✅
╚══════════════════════════════╝

🎯 Target: *≤ {target_price:.0f} MAD*
🛫 Agadir → Fez

"""
    
    if lowest_price:
        if lowest_price <= target_price:
            message += f"""
🎉 *GOOD NEWS!* Current lowest price is already at your target!
💰 Current: *{lowest_price:.2f} {currency}* on {lowest_date}
"""
        else:
            message += f"""
💰 Current lowest: *{lowest_price:.2f} {currency}*
📉 Difference: *{lowest_price - target_price:.2f} {currency}* to go
"""
    
    message += "\n💡 I'll notify you when the price drops to your target!"
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def my_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current alert status"""
    chat_id = str(update.effective_chat.id)
    
    if chat_id not in price_alerts or not price_alerts[chat_id].get("active"):
        await update.message.reply_text(
            "❌ You don't have an active price alert\n"
            "Use `/alert PRICE` to set one",
            parse_mode="Markdown"
        )
        return
    
    alert = price_alerts[chat_id]
    target = alert["target_price"]
    
    lowest_price, lowest_date, currency = get_current_lowest_price()
    
    message = f"""
╔══════════════════════════════╗
       🔔 *YOUR ALERT* 🔔
╚══════════════════════════════╝

🎯 Target: *≤ {target:.0f} MAD*
🛫 Agadir → Fez
✅ Status: *Active*

"""
    
    if lowest_price:
        status_emoji = "🎉" if lowest_price <= target else "⏳"
        message += f"""
💰 Current lowest: *{lowest_price:.2f} {currency}*
{status_emoji} {"Price is at your target!" if lowest_price <= target else f"Waiting for {lowest_price - target:.2f} EUR drop"}
"""
    
    await update.message.reply_text(message, parse_mode="Markdown")


async def stop_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop price alert"""
    chat_id = str(update.effective_chat.id)
    
    if chat_id in price_alerts:
        price_alerts[chat_id]["active"] = False
        save_alerts()
        await update.message.reply_text("✅ Price alert stopped!")
    else:
        await update.message.reply_text("❌ You don't have an active alert")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    chat_id = str(update.effective_chat.id)
    
    if query.data == "check_prices":
        await query.edit_message_text("🔍 Fetching prices... please wait...")
        result = get_flight_prices_formatted(30)
        await query.message.reply_text(result, parse_mode="Markdown")
        
    elif query.data == "lowest_price":
        await query.edit_message_text("🔍 Finding lowest price...")
        lowest_price, lowest_date, currency = get_current_lowest_price()
        
        if lowest_price:
            day_name = datetime.strptime(lowest_date, '%Y-%m-%d').strftime('%A')
            message = f"""
╔══════════════════════════════╗
     🏆 *BEST DEAL FOUND!* 🏆
╚══════════════════════════════╝

🛫 *Agadir* → *Fez*

💰 *{lowest_price:.2f} {currency}*
📅 {lowest_date} ({day_name})
"""
            await query.message.reply_text(message, parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ Could not fetch price")
            
    elif query.data.startswith("alert_"):
        target = float(query.data.split("_")[1])
        price_alerts[chat_id] = {
            "target_price": target,
            "active": True,
            "created": datetime.now().isoformat()
        }
        save_alerts()
        
        await query.edit_message_text(
            f"╔══════════════════════════════╗\n"
            f"     ✅ *ALERT ACTIVATED!* ✅\n"
            f"╚══════════════════════════════╝\n\n"
            f"🎯 Target: *≤ {target:.0f} MAD*\n"
            f"🛫 Agadir → Fez\n\n"
            f"🔔 _I'll notify you when price drops!_",
            parse_mode="Markdown"
        )


async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Background job to check prices and send alerts"""
    if not price_alerts:
        return
    
    lowest_price, lowest_date, currency = get_current_lowest_price()
    
    if not lowest_price:
        return
    
    for chat_id, alert in price_alerts.items():
        if not alert.get("active"):
            continue
            
        target = alert["target_price"]
        
        if lowest_price <= target:
            message = f"""
🚨 *PRICE ALERT!* 🚨
━━━━━━━━━━━━━━━━━━━━━━

🎯 Your target: *{target:.2f} EUR*
💰 Current price: *{lowest_price:.2f} {currency}*
📅 Date: *{lowest_date}*
✈️ Route: {ORIGIN} → {DESTINATION}

🎉 The price is at or below your target!

━━━━━━━━━━━━━━━━━━━━━━
🔗 Book now at ryanair.com
"""
            try:
                await context.bot.send_message(
                    chat_id=int(chat_id),
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error sending alert to {chat_id}: {e}")


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    WHITE = '\033[97m'


def print_banner():
    """Print aesthetic startup banner"""
    c = Colors
    print()
    print(f"{c.CYAN}{c.BOLD}╔══════════════════════════════════════════════════════════════╗{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}                                                              {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}   {c.YELLOW}✈️  {c.WHITE}{c.BOLD}R Y A N A I R   F L I G H T   B O T{c.RESET}   {c.YELLOW}✈️{c.RESET}            {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}                                                              {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}╠══════════════════════════════════════════════════════════════╣{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}                                                              {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}   {c.GREEN}🛫{c.RESET}  {c.WHITE}Agadir (AGA){c.RESET}  {c.DIM}─────────────►{c.RESET}  {c.WHITE}Fez (FEZ){c.RESET}  {c.GREEN}🛬{c.RESET}        {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}║{c.RESET}                                                              {c.CYAN}{c.BOLD}║{c.RESET}")
    print(f"{c.CYAN}{c.BOLD}╚══════════════════════════════════════════════════════════════╝{c.RESET}")
    print()


def print_status(message, status="info"):
    """Print formatted status messages"""
    c = Colors
    icons = {
        "info": f"{c.BLUE}ℹ️ {c.RESET}",
        "success": f"{c.GREEN}✅{c.RESET}",
        "warning": f"{c.YELLOW}⚠️ {c.RESET}",
        "error": f"{c.RED}❌{c.RESET}",
        "loading": f"{c.CYAN}⏳{c.RESET}",
        "bell": f"{c.YELLOW}🔔{c.RESET}",
        "rocket": f"{c.GREEN}🚀{c.RESET}",
    }
    icon = icons.get(status, icons["info"])
    print(f"  {icon} {message}")


def print_section(title):
    """Print a section header"""
    c = Colors
    print()
    print(f"  {c.DIM}{'─' * 50}{c.RESET}")
    print(f"  {c.BOLD}{c.WHITE}{title}{c.RESET}")
    print(f"  {c.DIM}{'─' * 50}{c.RESET}")


def main():
    """Start the bot"""
    c = Colors
    
    print_banner()
    
    if not BOT_TOKEN:
        print_section("⚙️  CONFIGURATION ERROR")
        print_status("TELEGRAM_BOT_TOKEN environment variable not set!", "error")
        print()
        print(f"  {c.YELLOW}To set up your bot:{c.RESET}")
        print(f"  {c.DIM}┌────────────────────────────────────────────────┐{c.RESET}")
        print(f"  {c.DIM}│{c.RESET} {c.WHITE}1.{c.RESET} Message {c.CYAN}@BotFather{c.RESET} on Telegram           {c.DIM}│{c.RESET}")
        print(f"  {c.DIM}│{c.RESET} {c.WHITE}2.{c.RESET} Create a new bot with {c.GREEN}/newbot{c.RESET}            {c.DIM}│{c.RESET}")
        print(f"  {c.DIM}│{c.RESET} {c.WHITE}3.{c.RESET} Copy the token and add to {c.YELLOW}.env{c.RESET} file:     {c.DIM}│{c.RESET}")
        print(f"  {c.DIM}│{c.RESET}    {c.GREEN}TELEGRAM_BOT_TOKEN=your_token_here{c.RESET}       {c.DIM}│{c.RESET}")
        print(f"  {c.DIM}└────────────────────────────────────────────────┘{c.RESET}")
        print()
        return
    
    # Load existing alerts
    load_alerts()
    alerts_count = sum(1 for a in price_alerts.values() if a.get("active"))
    
    print_section("🚀 STARTUP")
    print_status("Initializing bot...", "loading")
    print_status(f"Route: {c.BOLD}AGA{c.RESET} (Agadir) → {c.BOLD}FEZ{c.RESET} (Fez)", "info")
    print_status(f"Active alerts loaded: {c.BOLD}{alerts_count}{c.RESET}", "info")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("prices", prices_command))
    application.add_handler(CommandHandler("lowest", lowest_command))
    application.add_handler(CommandHandler("alert", set_alert_command))
    application.add_handler(CommandHandler("myalert", my_alert_command))
    application.add_handler(CommandHandler("stopalert", stop_alert_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add job to check prices every 30 minutes
    job_queue = application.job_queue
    job_queue.run_repeating(check_alerts_job, interval=1800, first=60)  # Every 30 min, start after 1 min
    
    print_section("✅ BOT READY")
    print_status("Bot is running!", "success")
    print_status("Price alerts check: every 30 minutes", "bell")
    print()
    print(f"  {c.DIM}┌────────────────────────────────────────────────┐{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}  {c.YELLOW}📱 Available Commands:{c.RESET}                         {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}                                                {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/start{c.RESET}     - Welcome message              {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/prices{c.RESET}    - All flight prices           {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/lowest{c.RESET}    - Best deal                   {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/alert{c.RESET}     - Set price alert             {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/myalert{c.RESET}   - Check your alert            {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}│{c.RESET}    {c.GREEN}/stopalert{c.RESET} - Disable alert               {c.DIM}│{c.RESET}")
    print(f"  {c.DIM}└────────────────────────────────────────────────┘{c.RESET}")
    print()
    print(f"  {c.DIM}Press {c.YELLOW}Ctrl+C{c.DIM} to stop the bot{c.RESET}")
    print()
    
    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
