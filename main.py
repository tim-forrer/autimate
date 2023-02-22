import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

client = discord.Client()

@bot.event
async def on_ready():
