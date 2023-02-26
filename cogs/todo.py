from typing import Optional, Any
import time
from datetime import datetime
import json
import os
from discord import app_commands, Interaction
from discord.ext import commands

time_format = "%Y-%m-%d %H:%M"

status_dict = {
    0: ":negative_squared_cross_mark:",
    1: ":atm:",
    2: ":white_check_mark:",
    3: ":pause_button:",
    4: ":wastebasket:",
}


class ToDoItem:
    def __init__(
        self,
        item_id: int,
        content: str,
        added_by: int,
        created: int,
        deadline: Optional[str],
        status: Optional[int],
    ):
        self.id = item_id
        self.content = content
        self.added_by = added_by
        self.created = created
        self.deadline: Optional[datetime] = self.get_deadline_obj(deadline)
        if status is None:
            self.status: int = 0
        else:
            self.status = status

    def status_str(self) -> str:
        return status_dict[self.status]

    def get_deadline_obj(self, deadline: Optional[str]) -> None:
        if deadline is None:
            return None
        return datetime.strptime(deadline, time_format)

    def __str__(self) -> str:
        if self.deadline is None:
            return f"{self.status_str()} {self.content} [#{self.id}]"
        return (
            f"{self.status_str()} {self.content} " +
            f"({self.deadline.strftime('%Y-%m-%d %H:%M')}) [#{self.id}]"
        )

    def update_status(self, new_status) -> None:
        try:
            assert new_status in status_dict.keys()
        except AssertionError:
            raise ValueError("Status must take value from 0-4 inclusive")
        self.status = new_status


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
        self.item_ids = self.get_item_ids()

    def get_item_ids(self) -> set[int]:
        ids: set[int] = set()
        for item in self.items:
            ids.add(item.id)
        return ids

    def get_next_item_id(self) -> int:
        for i in range(len(self.item_ids)):
            if i not in self.item_ids:
                return i
        return len(self.item_ids)

    def scope_str(self) -> str:
        scope_dict = {0: "User", 1: "Channel", 2: "Server"}
        return scope_dict[self.scope]

    def add_item(self, item: ToDoItem) -> None:
        self.items.append(item)

    def remove_item(self, item_id: int) -> Optional[ToDoItem]:
        self.items = [item for item in self.items if item.id != item_id]
        return self.get_item(item_id)

    def get_item(self, item_id: int) -> Optional[ToDoItem]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def __str__(self) -> str:
        string = f"List #{self.id} ({self.scope_str()} List)\n"
        for item in self.items:
            string += item.__str__() + "\n"
        return string


class ToDoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ToDoItem):
            dct = {
                "id": o.id,
                "type": "ToDoItem",
                "content": o.content,
                "added_by": o.added_by,
                "created": o.created,
                "deadline": o.deadline,
                "status": o.status,
            }
            if o.deadline is not None:
                dct["deadline"] = o.deadline.strftime(time_format)
            return dct
        elif isinstance(o, ToDoList):
            return {
                "id": o.id,
                "type": "ToDoList",
                "authors": o.authors,
                "scope": o.scope,
                "scope_id": o.scope_id,
                "items": [self.default(item) for item in o.items],
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


class ToDo(commands.GroupCog, name="todo"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    # Slash commands
    @app_commands.command(  # type: ignore
        name="create", description="Create a ToDo list for this channel."
    )
    async def create(
        self, interaction: Interaction,
        scope: Optional[int] = None, ephemeral: bool = True
    ) -> None:
        list_path = await self.get_list_path(interaction.user.id)
        if not os.path.exists(list_path):
            await self.make_lists_for_user(interaction.user.id)
            await self.write_to_list_file(interaction, [])
        # Figure out the scope_id
        if scope is None:
            scope = 1  # default to being a channel ToDoList
        scope_id = await self.get_scope_id(scope, interaction)

        # Verify a ToDoList with the same scope_id
        # for this user doesn't already exist
        lists = await self.get_lists_for_user(interaction)
        for list in lists:
            if list.scope_id == scope_id:
                await interaction.response.send_message(
                    f"There is already a list here with the same scope! \
                    (#{list.id})",
                    ephemeral=True
                )
                return

        # Make the new ToDoList
        this_id = await self.get_next_list_id()
        new_list = ToDoList(
            list_id=this_id,
            authors=[interaction.user.id],
            scope=scope,
            scope_id=scope_id,
            items=[],
        )
        lists.append(new_list)

        # Rewrite the users lists file with the new ToDoList appended
        await self.write_to_list_file(interaction, lists)

        await interaction.response.send_message(
            f"Created {new_list}",
            ephemeral=ephemeral
        )
        return

    @app_commands.command(  # type: ignore
        name="add", description="Add an item to a ToDo list."
    )
    async def add(
        self,
        interaction: Interaction,
        list_id: int,
        content: str,
        deadline: Optional[str] = None,
    ):
        # Load all the user lists
        lists = await self.get_lists_for_user(interaction)

        # Find the list with the given ID
        all_lists_with_id = [
            todolist for todolist in lists if todolist.id == list_id
        ]
        match len(all_lists_with_id):
            case 0:
                await interaction.response.send_message(
                    f"I could not find a list with ID {list_id} for \
                    {interaction.user.name}.",
                    ephemeral=True
                )
                return
            case 1:
                list_to_add_to = all_lists_with_id[0]
            case _:
                await interaction.response.send_message(
                    f"""I could not find a unique list of ID {list_id} \
                        for {interaction.user.name}.\n
                    Something has gone badly wrong...
                    """,
                    ephemeral=True
                )
                return

        new_item_id = list_to_add_to.get_next_item_id()
        new_item = ToDoItem(
            item_id=new_item_id,
            content=content,
            added_by=interaction.user.id,
            created=time.time_ns(),
            deadline=deadline,
            status=0,
        )
        list_to_add_to.add_item(new_item)

        # Write the lists back to file
        await self.write_to_list_file(interaction, lists)

        await interaction.response.send_message(
            f"Added to {list_to_add_to}",
            ephemeral=True
        )
        return

    @app_commands.command(  # type: ignore
        name="remove", description="Remove an item from a list."
    )
    async def remove(
        self, interaction: Interaction, list_id: int, item_id: int,
        ephemeral: bool = True
    ) -> None:
        todolist = await self.get_list_of_id(interaction, list_id)
        removed = todolist.remove_item(item_id)
        try:
            assert removed is not None
        except AssertionError:
            await interaction.response.send_message(
                f"Could not find item #{item_id} in list #{list_id}.",
                ephemeral=True
            )
            raise ValueError("List has no item of that id.")
        new_lists = await self.remove_list_of_id(interaction, list_id)
        new_lists.append(todolist)
        await self.write_to_list_file(interaction, new_lists)
        await interaction.response.send_message(
            f"Removed item successfully from {todolist}",
            ephemeral=ephemeral
        )
        return

    @app_commands.command(  # type: ignore
        name="delete", description="Delete a list."
    )
    async def delete(
            self,
            interaction: Interaction,
            list_id: int,
            ephemeral: bool = True
    ) -> None:
        new_lists = await self.remove_list_of_id(interaction, list_id)
        # Update the users lists file
        await self.write_to_list_file(interaction, new_lists)

        await interaction.response.send_message(
            f"List #{list_id} deleted successfully.",
            ephemeral=ephemeral
        )
        return

    @app_commands.command(  # type: ignore
            name="list", description="Show ToDo list"
        )
    async def show_list(
        self, interaction: Interaction, list_id: int, ephemeral: bool = True
    ) -> None:
        todolist = await self.get_list_of_id(interaction, list_id)
        await interaction.response.send_message(
            todolist, ephemeral=ephemeral
        )
        return

    @app_commands.command(  # type: ignore
            name="update",
            description=("Update item status." +
                         "0 (not started), 1 (in progress), "
                         "2 (done), 3 (on hold), " +
                         "4 (abandoned).")
            )
    async def update(
        self, interaction: Interaction, list_id: int, item_id: int,
        new_status: int = None, ephemeral: bool = True
    ):
        todolist = await self.get_list_of_id(interaction, list_id)
        item = todolist.get_item(item_id)
        if new_status is None:
            # Ensure a valid number is picked
            new_status = min(item.status + 1, 4)
        try:
            item.update_status(new_status)
        except ValueError:
            interaction.response.send_message("Invalid status provided")
        new_lists = await self.remove_list_of_id(interaction, list_id)
        new_lists.append(todolist)
        await self.write_to_list_file(interaction, new_lists)
        await interaction.response.send_message(
            f"Item updated\n{todolist}",
            ephemeral=ephemeral
        )
        return

    # Subroutines
    async def get_list_of_id(
        self, interaction: Interaction, list_id: int
    ) -> ToDoList:
        lists = await self.get_lists_for_user(interaction)
        for list in lists:
            if list.id == list_id:
                return list
        await interaction.response.send_message(
            f"{interaction.user.name} does not have a list of ID {list_id}.",
            ephemeral=True
        )
        raise ValueError("User has no list of specified ID")

    async def get_lists_for_user(
        self, interaction: Interaction
    ) -> list[ToDoList]:
        list_path = await self.get_list_path(interaction.user.id)
        try:
            assert os.path.exists(list_path)
        except AssertionError:
            await interaction.response.send_message(
                f"{interaction.user.name} doesn't have any lists!",
                ephemeral=True
            )
            raise ValueError("User has no associated list file.")

        with open(list_path, "r") as f:
            lists: list[ToDoList] = json.loads(f.read(), object_hook=as_todo)
        return lists

    async def make_lists_for_user(self, user_id: int) -> None:
        list_path = await self.get_list_path(user_id)
        if not os.path.exists(list_path):
            with open(list_path, "w") as _:
                pass
        return

    async def get_list_path(self, user_id) -> str:
        return f"lists/{user_id}.json"

    async def write_to_list_file(
        self, interaction: Interaction, lists: list[ToDoList]
    ) -> None:
        list_path = await self.get_list_path(interaction.user.id)
        await self.assert_path_exists(interaction, list_path)
        with open(list_path, "w") as f:
            json.dump(lists, f, cls=ToDoEncoder)
        return

    async def get_scope_id(self, scope: int, interaction: Interaction) -> int:
        # Check specified scope is allowed
        allowed_scopes = [0, 1, 2]
        try:
            assert scope in allowed_scopes
        except AssertionError:
            await interaction.response.send_message(
                "Invalid scope specified. Must take value of 0, 1 or 2.",
                ephemeral=True
            )
            raise ValueError("Invalid scope specified.")
        # Figure out the scope_id
        match scope:
            case 0:
                scope_id = interaction.user.id
            case 1:
                try:
                    assert interaction.channel_id is not None
                except AssertionError:
                    raise RuntimeError(
                        "I don't know why this would ever be None"
                    )
                scope_id = interaction.channel_id
            case 2:
                try:
                    assert interaction.guild_id is not None
                except AssertionError:
                    raise RuntimeError(
                        "I don't know why this would ever be None"
                    )
                scope_id = interaction.guild_id
        return scope_id

    async def get_next_list_id(self) -> int:
        # Get the next list id
        with open("bot_data.json", "r") as f:
            data = json.load(f)

        list_ids = data["all_list_ids"]
        # Find the smallest positive int that's not
        # already a list id.
        this_id = len(list_ids)
        for i in range(len(list_ids)):
            if i not in list_ids:
                this_id = i
                break
        data["all_list_ids"].append(this_id)

        # Update the bot data
        with open("bot_data.json", "w") as f:
            json.dump(data, f)
        return this_id

    async def assert_path_exists(
        self, interaction: Interaction, path: str
    ) -> None:
        try:
            assert os.path.exists(path)
        except AssertionError:
            await interaction.response.send_message(
                f"{interaction.user.name} doesn't have any lists!",
                ephemeral=True
            )
            raise ValueError("User has no associated list file.")

    async def remove_list_of_id(
        self, interaction: Interaction, list_id: int
    ) -> list[ToDoList]:
        # Load all user lists
        lists = await self.get_lists_for_user(interaction)
        # Remove the list of interest
        new_lists = [todolist for todolist in lists if todolist.id != list_id]

        try:
            assert len(lists) - 1 == len(new_lists)
            return new_lists
        except AssertionError:
            if len(lists) == len(new_lists):
                await interaction.response.send_message(
                    f"I could not find a list with ID {list_id} for \
                        {interaction.user.name}.",
                    ephemeral=True
                )
                raise ValueError("User has no list of specified ID.")
            else:
                await interaction.response.send_message(
                    f"""There are too many lists of id {list_id} for \
                        {interaction.user.name}.\n
                    Literally no clue how that has happened.
                    """,
                    ephemeral=True
                )
                raise ValueError("User has too many lists of specified ID.")
