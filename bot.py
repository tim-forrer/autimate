import discord
import json
import todo
from discord.ext import commands

bot = commands.Bot(intents=discord.Intents.all(), command_prefix="!")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord")

@bot.command(name="todo", help="Create and manage todo lists")
async def todo(ctx, param: str):
    response = param
    await ctx.send(response)