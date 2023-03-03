from multiprocessing.connection import wait
from re import T
from threading import Thread
from typing import Optional, Any
import time
import json
import os
from discord import SelectOption, app_commands, Interaction, abc
from discord.ext import commands
from classes.todoclass import *

class ToDo(commands.GroupCog, name="todo"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    # Slash commands
    @app_commands.command(  # type: ignore
        name="create", description="Create a ToDo list."
    )
    async def create(
        self,
        interaction: Interaction,
        name: Optional[str],
    ) -> None:
        if name is None:
            name = f"ToDoList for {interaction.user.name}"
        tdlist = ToDoList(
            list_id=await get_next_list_id(),
            name=name,
            author=interaction.user.name,
            author_id=interaction.user.id,
            items=[]
        )
        await write_list_to_user_file(interaction.user.id, tdlist=tdlist)
        await add_to_list_ids(tdlist.id)
        await interaction.response.send_message(f"{name} ToDo list created!", embed=tdlist.to_embed(), ephemeral=True)
    
    @app_commands.command(  # type: ignore
        name="delete", description="Delete a ToDo list."
    )
    async def delete(
        self,
        interaction: Interaction,
        list_id: int
    ) -> None:
        try:
            await remove_from_list_ids(list_id)
        except ValueError:
            emb = await self.get_users_lists_embed(interaction)
            await interaction.response.send_message(
                "I could not find a list with that ID.\n Here are all the lists you have and their ID's.",
                embed=emb,
                ephemeral=True
            )
            raise ValueError("User has no list of given ID.")
        user_lists = await load_user_lists(interaction.user.id)
        user_lists = [tdlist for tdlist in user_lists if tdlist != list_id]
        await write_lists_to_user_file(interaction.user.id, user_lists)
        emb = await self.get_users_lists_embed(interaction)
        await interaction.response.send_message(
            "List deleted. Here are your remaining lists.",
            embed=emb,
            ephemeral=True
        )
    
    @app_commands.command(  # type: ignore
            name = "show", description="Show all your ToDo lists"
    )
    async def show(self, interaction: Interaction) -> None:
        emb = await self.get_users_lists_embed(interaction)
        await interaction.response.send_message("Here you are", embed=emb, ephemeral=True)

    # Note this only raises an error if the user has no lists file
    # Hence an error is not raised after a list is deleted
    async def get_users_lists_embed(self, interaction: Interaction) -> Embed:
        try:
            lists = await load_user_lists(interaction.user.id)
        except ValueError:
            await interaction.response.send_message("You don't have any lists", ephemeral=True)
            raise ValueError("User didn't have any lists.")
        emb = Embed(
            colour=Colour.red(),
            title=f"{interaction.user.name}'s ToDo lists",
            description="Here's a list of your ToDoLists and their IDs."
        )
        for tdlist in lists:
            emb.add_field(name="\u200b", value=f"{tdlist.name} (#{tdlist.id})")
        return emb

