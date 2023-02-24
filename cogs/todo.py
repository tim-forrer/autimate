from typing import Optional, Any
import time
import json
import os
from discord import app_commands, Interaction, Object
from discord.ext import commands

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


class ToDo(commands.GroupCog, name="todo"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(  # type: ignore
            name="create_temp",
            description="Create a ToDo list for this channel."
    )
    async def create(
        self, interaction: Interaction, scope: Optional[int] = None
    ) -> None:
        if scope is None:
            scope = 1
        # Check specified scope is allowed
        allowed_scopes = [0, 1, 2]
        if scope not in allowed_scopes:
            await interaction.response.send_message(
                "Scope must be 0 (personal), 1 (channel) or 2 (server)."
            )
            return
        
        # Figure out the scope_id
        match scope:
            case 0:
                scope_id = interaction.user.id
            case 1:
                assert interaction.channel_id is not None
                scope_id = interaction.channel_id
            case 2:
                assert interaction.guild_id is not None
                scope_id = interaction.guild_id
        print(scope)

        # Find the path of the user's lists
        list_path = f"lists/{interaction.user.id}.json"
        # See if a file containing the user's lists already exists
        # If so read from that file
        # Else set lists to empty array (make the file later)
        if os.path.exists(list_path):
            with open(list_path, "r") as f:
                lists: list[ToDoList] = json.loads(
                    f.read(),
                    object_hook=as_todo  # Use custom decoder
                )
                # Check all the lists to see if one
                # with matching scope_id already exists
                for list in lists:
                    if list.scope_id == scope_id:
                        await interaction.response.send_message(
                            "There is already a list here!"
                        )
                        return
        else:
            lists = []
        
        # Get the next list id
        with open("bot_data.json", "r") as f:
            data = json.load(f)

        this_id = data["current_list_id"] + 1
        data["current_list_id"] = this_id
        data["all_list_ids"].append(this_id)
        
        # Update the bot data
        with open("bot_data.json", "w") as f:
            json.dump(data, f)

        new_list = ToDoList(
            list_id=this_id,
            authors=[interaction.user.id],
            scope=scope,
            scope_id=scope_id,
            items=[],
        )

        lists.append(new_list)

        with open(list_path, "w+") as f:
            json.dump(lists, f, cls=ToDoEncoder)

        await interaction.response.send_message(f"List created (#{this_id}).")
        return


class ToDoItem:
    def __init__(
        self,
        item_id: int,
        content: str,
        added_by: int,
        created: int,
        deadline: Optional[int],
        status: Optional[int],
    ):
        self.id = item_id
        self.content = content
        self.added_by = added_by
        self.created = created
        self.deadline = deadline
        if status is None:
            self.status: int = 0  # 0 = not started, 1 = in progress, 2 = completed, 3 = on hold, 4 = abandoned
        else:
            self.status = status

    def status_str(self) -> str:
        status_dict = {
            0: "Not started",
            1: "In progress",
            2: "Completed",
            3: "On hold",
            4: "Abandoned",
        }
        return status_dict[self.status]

    def __str__(self) -> str:
        return self.content + "(" + self.status_str() + ")"


class ToDoList:
    def __init__(
        self,
        list_id: int,
        authors: list[int],
        scope: int,  # 0 = user, 1 = channel, 2 = guild
        scope_id: int,
        items: list[ToDoItem],
    ):
        self.id = list_id
        self.authors = authors
        self.scope = scope
        self.items = items
        self.scope_id = scope_id

    def scope_str(self) -> str:
        scope_dict = {0: "User", 1: "Channel", 2: "Server"}
        return scope_dict[self.scope]

    def __str__(self) -> str:
        string = f"List #{self.id} (Scope: {self.scope_str()}) \n"
        for item in self.items:
            string += "\t- " + item.__str__() + "\n"
        return string


class ToDoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ToDoItem):
            return {
                "id": o.id,
                "type": "ToDoItem",
                "content": o.content,
                "added_by": o.added_by,
                "created": o.created,
                "deadline": o.deadline,
                "status": o.status,
            }
        elif isinstance(o, ToDoList):
            return {
                "id": o.id,
                "type": "ToDoList",
                "authors": o.authors,
                "scope": o.scope,
                "scope_id": o.scope_id,
                "items": [
                    self.default(item)
                    for item in o.items
                ],
            }
        return json.JSONEncoder.default(self, o)

def as_todo(dct: dict[Any, Any]) -> Any:
    if "type" in dct:
        if dct["type"] == "ToDoItem":
            return ToDoItem(
                item_id=dct["id"],
                content=dct["content"],
                added_by=dct["added_by"],
                created=dct["created"],
                deadline=dct["deadline"],
                status=dct["status"],
            )
        elif dct["type"] == "ToDoList":
            return ToDoList(
                list_id=dct["id"],
                authors=dct["authors"],
                scope=dct["scope"],
                scope_id=dct["scope_id"],
                items=dct["items"],
            )
    return dct
