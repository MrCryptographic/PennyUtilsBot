import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 1. Load the environment variables from your .env file
load_dotenv()

# 2. Set up the bot with required intents to see guilds
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def interactive_leave():
    print("\n--- Connected Servers ---")
    guilds = list(bot.guilds)
    
    if not guilds:
        print("The bot is not in any servers.")
        await bot.close()
        return

    # Print the numbered list of servers
    for index, guild in enumerate(guilds, start=1):
        print(f"[{index}] {guild.name} (ID: {guild.id})")
    
    print("[0] Exit script without leaving")

    # Handle the user choice in the terminal
    loop = asyncio.get_event_loop()
    try:
        choice = await loop.run_in_executor(None, input, "\nEnter the number of the server you want the bot to LEAVE: ")
        choice = int(choice)
        
        if choice == 0:
            print("Exiting without making changes...")
        elif 1 <= choice <= len(guilds):
            target_guild = guilds[choice - 1]
            print(f"Attempting to leave: {target_guild.name}...")
            await target_guild.leave()
            print("Successfully left the server.")
        else:
            print("Invalid choice. Number out of range.")
    except ValueError:
        print("Please enter a valid number.")
    
    # Close the bot connection gracefully and exit
    await bot.close()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Trigger the interactive menu as soon as the bot connects
    await interactive_leave()

# 3. Retrieve the token from your .env file
# Note: If your .env uses a different name like BOT_TOKEN, change 'TOKEN' below to match it.
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    print("Error: Could not find 'TOKEN' in your .env file.")
else:
    bot.run(TOKEN)
