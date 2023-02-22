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

def create_list(name: str, type: int):
    return

def delete_list():
    return

def add_to_list():
    return

def remove_from_list():
    return

def get_list():
    return

def make_public():
    return

def make_private():
    return

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
