
from __future__ import annotations

from abc import ABC, abstractmethod
from random import choice
import re
from typing import Callable, Type, Union

from game.Character import Character
from game.Item import Item, Item
from game.Map import Map
from game.State import State
    
class Valids:
    def __init__(self, allItems: list[Item], map: Map):
        self.charShorts: list[str] = []
        self.itemShorts: list[str] = []
        self.tagNames: list[str] = []
        self.items = allItems
        self.map = map
        self.allZoneNames = [zone.name for zone in map.zones]
        self.allItemNames = [i.string() for i in self.items]
        self.allItemTags: set[str] = set()
        for item in self.items:
            for tag in item.tags:
                self.allItemTags.add(tag)
    
    def addCharShort(self, short: str):
        if self.isValidCharShort(short): return False
        self.charShorts.append(short)
        return True
    
    def addItemShort(self, short: str):
        if self.isValidItemShort(short): return False
        self.itemShorts.append(short)
        return True
    
    def addTagName(self, name: str):
        if self.isValidTagName(name): return False
        self.tagNames.append(name)
        return True

    def isValidCharShort(self, short: str):
        return short in self.charShorts
    
    def isValidItemShort(self, short: str):
        return short in self.itemShorts
    
    def isValidTagName(self, name: str):
        return name in self.tagNames
    
    def isValidItem(self, name: str):
        return name in self.allItemNames
    
    def isValidTag(self, name: str):
        if name == "ANY":
            return True
        return name in self.allItemTags
    
    def isValidZone(self, name: str):
        return name in self.allZoneNames

    def getAllItemsWithTags(self, tags: list[str]):
        possItems = []
        for item in self.items:
            if item.hasAllTags(tags):
                possItems.append(item)
        return possItems
    
    def getItemWithName(self, name: str):
        # we've guaranteed the item name is valid when this is called
        for item in self.items:
            if item.string() == name:
                return [item]
    
    def getZoneWithName(self, name: str):
        for zone in self.map.zones:
            if zone.name == name:
                return zone

class EventPartException(Exception):
    pass

class EventPart(ABC):
    args: list[str]
    matches: list[str]
    
    @classmethod
    def match(cls, args: list[str]) -> bool:
        return any(args[0] == name for name in cls.matches)
    
    @classmethod
    def build(cls, args: list[str], valids: Valids):
        checkArgCount(args, cls.args)
        return cls(valids, *args)
    
    @abstractmethod
    def do(self, char: Character, state: State) -> Union[None, bool, str]:
        pass

def checkArgCount(args: list[str], argNames: list[str]):
    ct = len(argNames)
    argsStr = ", ".join(argNames)
    if not argNames[-1].startswith("*"):
        if argNames[-1].endswith("?"):
            if len(args) != ct and len(args) != ct - 1:
                raise EventPartException(f"Needs {ct - 1} or {ct} arguments ({len(args)} recieved): {argsStr}")
        else:
            if len(args) != ct:
                raise EventPartException(f"Needs {ct} arguments ({len(args)} recieved): {argsStr}")
    else:
        if argNames[-1].endswith("?"):
            ct -= 1
        if len(args) < ct:
            raise EventPartException(f"Needs {ct} or more arguments ({len(args)} recieved): {argsStr}")

def validateCharShort(name: str, valids: Valids):
    validate(valids.isValidCharShort, name, "character shorthand")
def validateItemShort(name: str, valids: Valids):
    validate(valids.isValidItemShort, name, "item shorthand")
def validateItemTag(name: str, valids: Valids):
    validate(valids.isValidTag, name, "item tag")
def validateItemName(name: str, valids: Valids):
    validate(valids.isValidItem, name, "specific item name")
def validateTagName(name: str, valids: Valids):
    validate(valids.isValidTagName, name, "tag name")
def validateZoneName(name: str, valids: Valids):
    validate(valids.isValidZone, name, "zone name")

def validate(fun: Callable, name: str, errName: str):
    if not fun(name):
        raise EventPartException(f"Encountered an invalid {errName}: `{name}`")

def addCharShortToValids(name: str, valids: Valids):
    addToValids(name, valids.addCharShort)
def addItemShortToValids(name: str, valids: Valids):
    addToValids(name, valids.addItemShort)
def addTagNameToValids(name: str, valids: Valids):
    addToValids(name, valids.addTagName)

def addToValids(name: str, addFun: Callable):
    if not addFun:
        raise EventPartException(f"Encountered an invalid addition name: `{name}`")
    if not addFun(name):
        raise EventPartException(f"Encountered a duplicate name: `{name}`")

def validateText(text: str, valids: Valids):
    textReplacePat = re.compile(r"([A-Za-z']*)(@|&)(\w+)")
    matches = textReplacePat.finditer(text)
    for match in matches:
        tag, objType, short = match.groups()
        if objType == "&":
            if tag != "" and not tag.lower() == "a":
                raise EventPartException(f"in text:\n    \"{text}\"\n    Encountered non-article conjugation for {tag}&{short}")
            if not valids.isValidItemShort(short):
                raise EventPartException(f"in text:\n    \"{text}\"\n    Encountered nonexistent item {tag}&{short}")
        elif objType == "@":
            if not valids.isValidCharShort(short):
                raise EventPartException(f"in text:\n    \"{text}\"\n    Encountered nonexistent character {tag}@{short}")

class Suite:
    def __init__(self, charShort: str, eventPartClasses: list[Type[EventPart]], epArgLists: list[list[str]], valids: Valids):
        self.eventPartClasses = eventPartClasses
        self.charShort = charShort
        self.valids = valids
        
        self.eventParts: list[EventPart] = []
        
        self.valids.addCharShort(self.charShort)
        self.parse(epArgLists)
    
    def getCharShort(self):
        return self.charShort
    
    def getValids(self):
        return self.valids
    
    def exception(self, reqs: list[list[str]], args: list[str], e: Union[Exception, str]):
        reqsStr = ""
        for req in reqs:
            if args == req:
                reqsStr += f"->"
            reqsStr += " ".join(req) + ", "
        reqsStr = reqsStr[:-2]
        return Exception(f"in line \"{self.charShort}: {reqsStr}\"\n    {e}")
    
    def parse(self, reqs: list[list[str]]):
        for args in reqs:
            found = False
            for reqClass in self.eventPartClasses:
                if reqClass.match(args):
                    try:
                        ep = reqClass.build(args, self.valids)
                    except EventPartException as e:
                        raise self.exception(reqs, args, e)
                    self.eventParts.append(ep)
                    found = True
                    break
            if not found:
                raise self.exception(reqs, args, "Not recognized as a valid event part")

    def check(self, char: Character, state: State):
        for ep in self.eventParts:
            if not ep.do(char, state):
                return False
        return True
    
    def perform(self, char: Character, state: State):
        allRes: list[str] = []
        for ep in self.eventParts:
            res = ep.do(char, state)
            allRes.append(res)
        return allRes
