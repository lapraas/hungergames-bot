
from __future__ import annotations

from typing import Type

from Item import Item
from Character import Character
from State import State
from Valids import EventPart, Valids, validateCharShort, validateItemShort, validateTagName, validateZoneName

class TagRes(EventPart):
    args = ["type", "tag name"]
    matches = ["tag"]
        
    def __init__(self, valids: Valids, *args: str):
        _, self.tag = args
    
    def do(self, char: Character, state: State):
        char.addTag(self.tag)
        return f"added tag: {self.tag}"

class UntagRes(EventPart):
    args = ["type", "tag name"]
    matches = ["untag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.tag = args
        validateTagName(self.tag, valids)
    
    def do(self, char: Character, state: State):
        char.removeTag(self.tag)
        return f"removed tag: {self.tag}"

class ItemRes(EventPart):
    args = ["type", "item shorthand"]
    matches = ["give"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
    
    def do(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.copyAndGiveItem(item)
        return f"gave item: {item}"

class AllyRes(EventPart):
    args = ["type", "char shorthand"]
    matches = ["ally"]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.charShort = args
        validateCharShort(self.charShort, valids)
    
    def do(self, char: Character, state: State):
        toAlly = state.getChar(self.charShort)
        if char.isAlone() and toAlly.isAlone():
            alliance = []
            char.joinAlliance(alliance)
            toAlly.joinAlliance(alliance)
            return f"allied with: {toAlly}"
        elif not char.isAlone():
            alliance = char.getAlliance()
            toAlly.leaveAlliance()
            toAlly.joinAlliance(alliance)
            return f"alliance joined by: {toAlly}"
        elif not toAlly.isAlone():
            alliance = toAlly.getAlliance()
            char.leaveAlliance()
            char.joinAlliance(alliance)
            return f"allied with: {toAlly}"

class LeaveRes(EventPart):
    args = ["type"]
    matches = ["leave"]
    
    def __init__(self, *_):
        pass
    
    def do(self, char: Character, state: State):
        char.leaveAlliance()
        return "left alliance"

class ConsumeRes(EventPart):
    args = ["type", "item shorthand"]
    matches = ["consume"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
        validateItemShort(self.itemShort, valids)
    
    def do(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.takeItem(item)
        return f"consumed item: {item}"

class MoveRes(EventPart):
    args = ["type", "zone name?"]
    matches = ["move"]
    
    def __init__(self, valids: Valids, *args: str):
        self.zone = None
        if len(args) >= 2:
            zoneName = args[1]
            validateZoneName(zoneName, valids)
            self.zone = valids.getZoneWithName(zoneName)
    
    def do(self, char: Character, state: State):
        if self.zone:
            char.move(self.zone)
        else:
            char.moveRandom()
        return f"moved to zone: {char.getLocation().name}"

ALLRESCLASSES: list[Type[EventPart]] = [
    TagRes,
    UntagRes,
    ItemRes,
    AllyRes,
    LeaveRes,
    ConsumeRes,
    MoveRes
]
