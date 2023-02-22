import discord
import json
from todo import ToDo
from discord.ext.commands import Bot, Context

bot = Bot(intents=discord.Intents.all(), command_prefix="!")

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord")
    with open ("bot_data.json", "r") as f:
        bot_data = json.load(f)
    print(f"Current list ID is {bot_data['current_list_id']}")
    await bot.add_cog(ToDo(bot))
