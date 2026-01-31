import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Load cogs
async def load_cogs():
    await bot.load_extension('cogs.match_commands')
    await bot.load_extension('cogs.profile_commands')
    await bot.load_extension('cogs.team_commands')
    await bot.load_extension('cogs.help_commands')

@bot.event
async def setup_hook():
    await load_cogs()

if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file")
    else:
        bot.run(TOKEN)