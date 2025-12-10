#!/usr/bin/env python3
"""
✈️ Ryanair Flight Price Discord Bot
Clean, minimal implementation for tracking Agadir → Fez flights
"""

import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from dotenv import load_dotenv
from ryanair_api import RyanairAPI

load_dotenv()

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALERTS_FILE = "alerts.json"
ORIGIN, DESTINATION = "AGA", "FEZ"

# Colors
class Color:
    PRIMARY = 0x5865F2
    SUCCESS = 0x57F287
    WARNING = 0xFEE75C
    ERROR = 0xED4245
    GOLD = 0xF1C40F

# Terminal colors
class C:
    CYAN, GREEN, YELLOW, RED, WHITE = '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[97m'
    BOLD, DIM, R = '\033[1m', '\033[2m', '\033[0m'

# Alerts storage
alerts = {}

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def load_alerts():
    global alerts
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE) as f:
                alerts = json.load(f)
    except: alerts = {}

def save_alerts():
    try:
        with open(ALERTS_FILE, 'w') as f:
            json.dump(alerts, f, indent=2)
    except: pass

def get_flights(days=30):
    """Fetch flight prices"""
    api = RyanairAPI()
    try:
        data = api.get_cheapest_fares(ORIGIN, DESTINATION, datetime.now().strftime("%Y-%m-%d"), days)
        fares = data.get("outbound", {}).get("fares", [])
        return sorted([
            {"date": f["day"], "price": f["price"]["value"], "currency": f["price"]["currencyCode"],
             "dep": f["departureDate"][11:16] if f.get("departureDate") else "N/A",
             "arr": f["arrivalDate"][11:16] if f.get("arrivalDate") else "N/A"}
            for f in fares if f and f.get("price") and not f.get("unavailable")
        ], key=lambda x: x["price"])
    except:
        return []

def get_lowest():
    """Get lowest price flight"""
    flights = get_flights()
    return flights[0] if flights else None

# ══════════════════════════════════════════════════════════════
# BOT SETUP
# ══════════════════════════════════════════════════════════════

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ══════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════

class MainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🏆 Best Price", style=discord.ButtonStyle.success)
    async def best_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.send(embed=make_lowest_embed())

    @discord.ui.button(label="📊 All Prices", style=discord.ButtonStyle.primary)
    async def all_prices(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.followup.send(embed=make_prices_embed())

    @discord.ui.button(label="🔔 Set Alert", style=discord.ButtonStyle.secondary)
    async def set_alert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AlertModal())


class AlertModal(discord.ui.Modal, title="🔔 Set Price Alert"):
    price = discord.ui.TextInput(label="Target Price (MAD)", placeholder="165", max_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target = float(self.price.value)
            alerts[str(interaction.user.id)] = {
                "price": target, "channel": interaction.channel_id, "active": True
            }
            save_alerts()
            
            embed = discord.Embed(title="✅ Alert Set!", color=Color.SUCCESS)
            embed.description = f"You'll be notified when price ≤ **{target:.0f} MAD**"
            
            lowest = get_lowest()
            if lowest and lowest["price"] <= target:
                embed.add_field(name="🎉 Already at target!", 
                    value=f"Current: **{lowest['price']:.2f} MAD**", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Invalid price", ephemeral=True)

# ══════════════════════════════════════════════════════════════
# EMBED BUILDERS
# ══════════════════════════════════════════════════════════════

def make_welcome_embed():
    lowest = get_lowest()
    embed = discord.Embed(title="✈️ RYANAIR FLIGHT TRACKER", color=Color.PRIMARY)
    embed.description = "Track **Agadir → Fez** flight prices"
    embed.add_field(name="🛫 Route", value="```AGA ══════► FEZ```", inline=False)
    
    if lowest:
        day = datetime.strptime(lowest['date'], '%Y-%m-%d').strftime('%A')
        embed.add_field(name="🏆 Best Price", value=f"**{lowest['price']:.2f} MAD**", inline=True)
        embed.add_field(name="📅 Date", value=f"{lowest['date']} ({day})", inline=True)
        embed.add_field(name="🕐 Time", value=f"{lowest['dep']} → {lowest['arr']}", inline=True)
    
    embed.add_field(name="📆 Schedule", 
        value="```Sat: 09:35→10:55  |  Tue: 10:05→11:25```", inline=False)
    embed.set_footer(text="Use buttons below or /help for commands")
    return embed

def make_lowest_embed():
    lowest = get_lowest()
    if not lowest:
        return discord.Embed(title="❌ No flights found", color=Color.ERROR)
    
    day = datetime.strptime(lowest['date'], '%Y-%m-%d').strftime('%A')
    embed = discord.Embed(title="🏆 BEST DEAL!", color=Color.GOLD)
    embed.add_field(name="💰 Price", value=f"**{lowest['price']:.2f} MAD**", inline=True)
    embed.add_field(name="📅 Date", value=f"{lowest['date']} ({day})", inline=True)
    embed.add_field(name="🕐 Time", value=f"{lowest['dep']} → {lowest['arr']}", inline=True)
    return embed

def make_prices_embed(limit=None):
    flights = get_flights()
    if not flights:
        return discord.Embed(title="❌ No flights", color=Color.ERROR)
    
    if limit:
        flights = [f for f in flights if f["price"] <= limit]
        if not flights:
            return discord.Embed(title=f"❌ No flights under {limit} MAD", color=Color.WARNING)
    
    lowest = flights[0]["price"]
    embed = discord.Embed(
        title=f"📊 {'Filtered' if limit else 'All'} Flights",
        description=f"Found **{len(flights)}** flights",
        color=Color.PRIMARY
    )
    
    lines = []
    for f in sorted(flights[:15], key=lambda x: x["date"]):
        emoji = "🟢" if f["price"] == lowest else "⚪"
        day = datetime.strptime(f['date'], '%Y-%m-%d').strftime('%a')
        lines.append(f"{emoji} `{f['date']}` {day} {f['dep']} │ **{f['price']:.0f}** MAD")
    
    embed.add_field(name="Flights", value="\n".join(lines), inline=False)
    embed.set_footer(text="🟢 = Best price")
    return embed

def make_stats_embed():
    flights = get_flights(60)
    if not flights:
        return discord.Embed(title="❌ No data", color=Color.ERROR)
    
    prices = [f["price"] for f in flights]
    embed = discord.Embed(title="📈 STATISTICS", color=Color.PRIMARY)
    embed.add_field(name="Price Range",
        value=f"```▼ Low:  {min(prices):.2f} MAD\n▲ High: {max(prices):.2f} MAD\n◆ Avg:  {sum(prices)/len(prices):.2f} MAD```",
        inline=False)
    embed.add_field(name="Total Flights", value=f"**{len(flights)}**", inline=True)
    embed.add_field(name="Best Day", value=flights[0]["date"], inline=True)
    return embed

# ══════════════════════════════════════════════════════════════
# SLASH COMMANDS
# ══════════════════════════════════════════════════════════════

@bot.tree.command(name="start", description="🏠 Main menu")
async def cmd_start(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_welcome_embed(), view=MainView())

@bot.tree.command(name="prices", description="📊 All flight prices")
async def cmd_prices(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(embed=make_prices_embed())

@bot.tree.command(name="lowest", description="🏆 Best price")
async def cmd_lowest(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(embed=make_lowest_embed())

@bot.tree.command(name="stats", description="📈 Statistics")
async def cmd_stats(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(embed=make_stats_embed())

@bot.tree.command(name="alert", description="🔔 Set price alert")
@app_commands.describe(price="Target price in MAD")
async def cmd_alert(interaction: discord.Interaction, price: float):
    alerts[str(interaction.user.id)] = {"price": price, "channel": interaction.channel_id, "active": True}
    save_alerts()
    
    embed = discord.Embed(title="✅ Alert Set!", color=Color.SUCCESS)
    embed.description = f"Notify when price ≤ **{price:.0f} MAD**"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="myalert", description="🔔 Check your alert")
async def cmd_myalert(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid not in alerts or not alerts[uid].get("active"):
        await interaction.response.send_message("❌ No active alert. Use `/alert`", ephemeral=True)
        return
    
    target = alerts[uid]["price"]
    lowest = get_lowest()
    
    embed = discord.Embed(title="🔔 Your Alert", color=Color.PRIMARY)
    embed.add_field(name="Target", value=f"≤ **{target:.0f} MAD**", inline=True)
    embed.add_field(name="Status", value="✅ Active", inline=True)
    
    if lowest:
        status = "🎉 Reached!" if lowest["price"] <= target else f"⏳ {lowest['price'] - target:.0f} MAD to go"
        embed.add_field(name="Current", value=f"**{lowest['price']:.2f} MAD** ({status})", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="stopalert", description="🔕 Stop alert")
async def cmd_stopalert(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid in alerts:
        alerts[uid]["active"] = False
        save_alerts()
    await interaction.response.send_message("✅ Alert disabled", ephemeral=True)

@bot.tree.command(name="help", description="❓ Commands")
async def cmd_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 Commands", color=Color.PRIMARY)
    embed.description = """
`/start` - Main menu
`/prices` - All flights
`/lowest` - Best deal
`/stats` - Statistics
`/alert <price>` - Set alert
`/myalert` - Check alert
`/stopalert` - Disable alert
"""
    await interaction.response.send_message(embed=embed)

# ══════════════════════════════════════════════════════════════
# BACKGROUND TASK
# ══════════════════════════════════════════════════════════════

@tasks.loop(minutes=30)
async def check_alerts():
    lowest = get_lowest()
    if not lowest:
        return
    
    for uid, data in list(alerts.items()):
        if not data.get("active") or lowest["price"] > data["price"]:
            continue
        
        channel = bot.get_channel(data["channel"])
        if channel:
            embed = discord.Embed(title="🚨 PRICE ALERT!", color=Color.GOLD)
            embed.description = f"<@{uid}> Target reached!"
            embed.add_field(name="Target", value=f"**{data['price']:.0f} MAD**", inline=True)
            embed.add_field(name="Current", value=f"**{lowest['price']:.2f} MAD**", inline=True)
            embed.add_field(name="Date", value=lowest["date"], inline=True)
            await channel.send(embed=embed)

@check_alerts.before_loop
async def before_check():
    await bot.wait_until_ready()

# ══════════════════════════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"\n{C.CYAN}{'═'*50}{C.R}")
    print(f"{C.CYAN}  ✈️  RYANAIR DISCORD BOT{C.R}")
    print(f"{C.CYAN}{'═'*50}{C.R}")
    print(f"{C.GREEN}  ✓{C.R} Logged in as {C.BOLD}{bot.user.name}{C.R}")
    print(f"{C.GREEN}  ✓{C.R} Servers: {len(bot.guilds)}")
    
    try:
        # Clear guild-specific commands (these cause duplicates)
        for guild in bot.guilds:
            await bot.http.bulk_upsert_guild_commands(bot.application_id, guild.id, [])
        print(f"{C.YELLOW}  ⟳{C.R} Cleared guild commands")
        
        # Sync global commands only
        synced = await bot.tree.sync()
        print(f"{C.GREEN}  ✓{C.R} Synced {len(synced)} global commands")
    except Exception as e:
        print(f"{C.RED}  ✗{C.R} Sync failed: {e}")
    
    check_alerts.start()
    print(f"{C.GREEN}  ✓{C.R} Alert checker started (30 min)")
    print(f"\n{C.DIM}  Commands: /start /prices /lowest /stats /alert /help{C.R}\n")

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    if not BOT_TOKEN:
        print(f"\n{C.RED}  ✗ DISCORD_BOT_TOKEN not set!{C.R}")
        print(f"\n  {C.YELLOW}Setup:{C.R}")
        print(f"  1. Go to discord.com/developers/applications")
        print(f"  2. Create bot → Copy token")
        print(f"  3. Add to .env: DISCORD_BOT_TOKEN=your_token\n")
        return
    
    load_alerts()
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
