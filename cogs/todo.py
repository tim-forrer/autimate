from multiprocessing.connection import wait
from re import T
from threading import Thread
from typing import Optional, Any
import time
import json
import os
from xml.dom import EMPTY_NAMESPACE
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
            await self.no_list_of_id(interaction)
        user_lists = await load_user_lists(interaction.user.id)
        user_lists = [tdlist for tdlist in user_lists if tdlist.id != list_id]
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
    async def show(self, interaction: Interaction, list_id: Optional[int]) -> None:
        if list_id is None:
            emb = await self.get_users_lists_embed(interaction)
            await interaction.response.send_message("Here you are", embed=emb, ephemeral=True)
            return
        tdlist = await load_list_of_id(interaction.user.id, list_id)
        await interaction.response.send_message("Here you are", embed=tdlist.to_embed(), ephemeral=True)

    
    @app_commands.command(  # type: ignore
        name="add", description="Add an item to a ToDo list, deadline is of format YYYY-MM-DD HH:MM"
    )
    async def add(self, interaction: Interaction, list_id: int, content: str, deadline: Optional[str]) -> None:
        tdlist: ToDoList = await load_list_of_id(interaction.user.id, list_id)
        tditem = ToDoItem(
            tdlist.get_next_item_id(),
            status=0,
            content=content,
            deadline=deadline
        )
        tdlist.add_item(tditem)
        await write_list_to_user_file(interaction.user.id, tdlist)
        emb = tdlist.to_embed()
        await interaction.response.send_message(content="Added item to list.", embed=emb, ephemeral=True)

    @app_commands.command(  # type: ignore
        name="remove", description="Remove a list item from a list."
    )
    async def remove(self, interaction: Interaction, list_id: int, item_id: int) -> None:
        try:
            tdlist: ToDoList = await load_list_of_id(interaction.user.id, list_id)
        except ValueError:
            await self.no_list_of_id(interaction)
        item: Optional[ToDoItem] = tdlist.remove_item(item_id)
        if item is None:
            await self.no_item_of_id(interaction, tdlist)
        else:
            emb = tdlist.to_embed()
            await write_list_to_user_file(interaction.user.id, tdlist)
            await interaction.response.send_message(
                content="Removed successfully.",
                embed=emb
            )
    
    @app_commands.command(  # type: ignore
            name="update", description="Update the status of an item (takes values 0-4)."
        )
    async def update(self, interaction: Interaction, list_id: int, item_id: int, new_status: int) -> None:
        tdlist = await load_list_of_id(interaction.user.id, list_id)
        item = tdlist.get_item(item_id)
        if item is None:
            emb = tdlist.to_embed()
            await interaction.response.send_message("I could not find an item with that ID. Here's your list again.", embed=emb, ephemeral=True)
            raise ValueError("No list item of given ID.")
        try:
            item.update_status(new_status)
        except ValueError:
            await interaction.response.send_message("Invalid status given - must take value from [0, 4]", ephemeral=True)
        await write_list_to_user_file(interaction.user.id, tdlist)
        emb = tdlist.to_embed()
        await interaction.response.send_message("Status updated.", embed=emb, ephemeral=True)
        
        
    async def no_list_of_id(self, interaction: Interaction):
        emb = await self.get_users_lists_embed(interaction)
        await interaction.response.send_message(
            "I could not find a list with that ID.\n Here are all the lists you have and their IDs.",
            embed=emb,
            ephemeral=True
        )
        raise ValueError("User has no list of given ID.")
    
    async def no_item_of_id(self, interaction: Interaction, tdlist: ToDoList):
        emb = tdlist.to_embed()
        await interaction.response.send_message(
            "There doesn't seem to be an item of that ID in that list, I'm showing it below",
            embed=emb,
            ephemeral=True
        )
        raise ValueError("User has no item of that ID in the list")

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

