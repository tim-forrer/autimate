from typing import Optional
import time
import json
# 
# Module that contains code relevant for todo list handling
# Lists are stored as JSONs
# Data is something like
# Title (ID)
# [ ] Item 0
# [X] Item 1
# etc...

# Create a list
# Option to make it a private/public
# - Server wide list (0)
# - Channel list (1)
# - Personal list (2)

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


class ToDoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(obj, ToDoItem):
            return obj.to_json()
        return json.JSONEncoder.default(self, o)

class ToDoItem():
    def __init__(
        self,
        id: int,
        content: str,
        added_by: int,
        created: int,
        deadline: Optional[int],
        status: int,
    ):
        self._id = _id
        self.content = content
        self.added_by = added_by
        self.created = created
        self.deadline = deadline
    
    def to_json(self) -> str:
        return json.dumps(self)
    
class ToDoList():
    def __init__(
        self,
        id: int,
        name: Optional[str],
        authors: list[int],
        type: int,
        is_private: bool,
        items: list[ToDoItem],
    ):
        self.id = id
        self.name = name
        self.authors = authors
        self.type = type
        self.is_private = is_private
        self.items = items
    
    def to_json(self) -> str:
        return json.dumps(self)
