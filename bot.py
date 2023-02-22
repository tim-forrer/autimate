import discord
import json
import todo
from discord.ext.commands import Bot, Context

bot = Bot(intents=discord.Intents.all(), command_prefix="!")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord")

@bot.group(pass_context=True)
async def todo(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid subcommand passed.")

@todo.group()
async def help(ctx: Context):
    await ctx.send("Sending help")

@todo.group()
async def create(ctx: Context):
    await ctx.send("Creating list")

@todo.group()
async def delete(ctx: Context):
    await ctx.send("Deleting list")

@todo.group()
async def add(ctx: Context):
    await ctx.send("Adding to list")

@todo.group()
async def remove(ctx: Context):
    await ctx.send("Removing from list")

@todo.group()
async def get(ctx: Context):
    await ctx.send("Getting list")

@todo.group(pass_context=True)
async def make(ctx: Context):
    if ctx.invoked_subcommand is None:
        await ctx.send("Invalid subcommand passed.")

@make.group()
async def public(ctx: Context):
    await ctx.send("Now public")

@make.group()
async def private(ctx: Context):
    await ctx.send("Now private")
