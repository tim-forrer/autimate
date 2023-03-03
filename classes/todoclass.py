from datetime import datetime, date
from typing import Optional, Any
import json
from dotenv import load_dotenv
import os
from discord import Embed, Colour

# Get environment variables
TIME_FORMAT = "%Y-%m-%d %H:%M"
STATUS_DICT = {0: ":negative_squared_cross_mark:",1: ":atm:",2: ":white_check_mark:",3: ":pause_button:",4: ":wastebasket:"}
STATUS_DICT_TXT = {0: "Not Started",1: "In Progress",2: "Done",3: "Paused",4: "Abandoned"}
LISTS_DIR = "lists/{user_id}.json"
BOT_DATA = "bot_data.json"

class ToDoItem:
    def __init__(
        self,
        item_id: int,
        status: Optional[int],
        content: str,
        deadline: Optional[str],
    ):
        self.id = item_id
        self.content = content
        self.deadline: Optional[datetime] = self.get_deadline_obj(deadline)
        if status is None:
            self.status: int = 0
        else:
            self.status = status

    def status_str(self) -> str:
        return STATUS_DICT[self.status]

    def get_deadline_obj(self, deadline: Optional[str]) -> Optional[datetime]:
        if deadline is None:
            return None
        return datetime.strptime(deadline, TIME_FORMAT)

    def __str__(self) -> str:
        string = f"{self.status_str()} {self.content}"
        if self.deadline is not None:
            string += f"({self.deadline.strftime('%Y-%m-%d %H:%M')})"
        return string

    def update_status(self, new_status) -> None:
        try:
            assert new_status in STATUS_DICT.keys()
        except AssertionError:
            raise ValueError("Status must take value from 0-4 inclusive")
        self.status = new_status


class ToDoList:
    def __init__(
        self,
        list_id: int,
        name: str,
        author: str,
        author_id: int,
        items: list[ToDoItem],
    ):
        self.id = list_id
        self.name = name
        self.author = author
        self.author_id = author_id
        self.items = items
        self.item_ids = self.get_item_ids()
    
    def __str__(self) -> str:
        string = f"{self.name} (created by {self.author}\n"
        for item in self.items:
            string += item.__str__() + "\n"
        return string

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
    
    def get_items_grouped(self) -> dict[int, list[ToDoItem]]:
        grouped: dict[int, list[ToDoItem]] = dict()
        for i in STATUS_DICT.keys():
            grouped[i] = []
            for tditem in self.items:
                if tditem.id == i:
                    grouped[i].append(tditem)
        return grouped
    
    def to_embed(self) -> Embed:
        emb = Embed(
            title = self.name,
            colour=Colour.blue(),
            description=self.author
        )
        grouped = self.get_items_grouped()
        for i in STATUS_DICT_TXT:
            for j, tditem in enumerate(grouped[i]):
                if j == 0:
                    emb.add_field(name=STATUS_DICT_TXT[i], value=tditem)
                else:
                    emb.add_field(name="\u200b", value=tditem)
        emb.set_footer(text = f"List ID {self.id}")
        return emb



class ToDoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ToDoItem):
            dct = {
                "id": o.id,
                "type": "ToDoItem",
                "content": o.content,
                "deadline": o.deadline,
                "status": o.status,
            }
            if o.deadline is not None:
                dct["deadline"] = o.deadline.strftime(TIME_FORMAT)
            return dct
        elif isinstance(o, ToDoList):
            return {
                "type": "ToDoList",
                "id": o.id,
                "name": o.name,
                "author": o.author,
                "author_id": o.author_id,
                "items": [self.default(item) for item in o.items],
            }
        return json.JSONEncoder.default(self, o)

def as_todo(dct: dict[Any, Any]) -> Any:
    if "type" in dct:
        if dct["type"] == "ToDoItem":
            return ToDoItem(
                item_id=dct["id"],
                content=dct["content"],
                deadline=dct["deadline"],
                status=dct["status"],
            )
        elif dct["type"] == "ToDoList":
            return ToDoList(
                list_id=dct["id"],
                name=dct["name"],
                author=dct["author"],
                author_id=dct["author_id"],
                items=dct["items"],
            )
    return dct

async def get_user_file_path(user_id: int) -> str:
        return LISTS_DIR.replace("{user_id}", str(user_id))

async def load_user_lists(user_id: int) -> list[ToDoList]:
        user_file_path = await get_user_file_path(user_id)
        if not os.path.exists(user_file_path):
            return []
        with open(user_file_path, "r") as f:
            user_lists: list[ToDoList] = json.load(f, object_hook=as_todo)
        return user_lists

async def load_list_of_id(self, user_id: int, list_id: int) -> ToDoList:
    user_lists: list[ToDoList] = await load_user_lists(user_id)
    for tdlist in user_lists:
        if tdlist.id == list_id:
            return tdlist
    raise ValueError("Could not find list of the given ID for this user.")

async def write_list_to_user_file(user_id: int, tdlist: ToDoList) -> None:
    user_lists = await load_user_lists(user_id)
    user_lists = [other_tdlist for other_tdlist in user_lists if tdlist.id != other_tdlist.id]
    await write_lists_to_user_file(user_id, user_lists)
    return

async def write_lists_to_user_file(user_id: int, tdlists: list[ToDoList]) -> None:
    user_file_path = await get_user_file_path(user_id)
    with open(user_file_path, "w") as f:
        json.dump(tdlists, f, cls=ToDoEncoder)
    return

async def get_next_list_id() -> int:
    with open(BOT_DATA, "r") as f:
        all_ids = json.load(f)["all_list_ids"]    
    next_id = len(all_ids)
    for i in range(next_id):
        if i not in all_ids:
            return i
    return next_id

async def add_to_list_ids(list_id: int) -> None:
    with open(BOT_DATA, "r") as f:
        all_ids_arr = json.load(f)
    
    all_ids: list[int] = all_ids_arr["all_list_ids"]
    if list_id in all_ids:
        raise ValueError("This list ID is already present for another list")
    all_ids.append(list_id)
    with open(BOT_DATA, "w") as f:
        json.dump(all_ids_arr, f)
    return

async def remove_from_list_ids(list_id: int) -> None:
    with open(BOT_DATA, "r") as f:
        all_ids_arr = json.load(f)
        print(all_ids_arr)
    
    all_ids: list[int] = all_ids_arr["all_list_ids"]
    if list_id not in all_ids:
        raise ValueError("This list ID is not already present")
    all_ids.remove(list_id)
    with open(BOT_DATA, "w") as f:
        json.dump(all_ids_arr, f)
        print(all_ids_arr)
    return
