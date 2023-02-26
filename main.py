import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from cogs.todo import ToDo

# Get environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")
APP_ID = os.getenv("APP_ID")

assert TOKEN is not None
assert SERVER_ID is not None

guild = discord.Object(SERVER_ID)

bot = commands.Bot(
    command_prefix="!", intents=discord.Intents.all(), application_id=APP_ID
)


@bot.event
async def on_ready():
    await bot.add_cog(ToDo(bot), guild=guild)
    print(f"{bot.user.name} has connected to Discord")


@bot.command(name="sync")  # type: ignore
async def sync(ctx: commands.Context):
    print("Sync started")
    await bot.tree.sync(guild=guild)
    await ctx.send("Synced")


@bot.command(name="syncglobal")  # type: ignore
async def syncglobal(ctx: commands.Context):
    print("Global sync started")
    await bot.tree.sync()
    await ctx.send("Synced global (may take a while to reflect.)")


bot.run(TOKEN)
