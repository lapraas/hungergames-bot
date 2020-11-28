
from __future__ import annotations

import re
from typing import Callable, Type, Union

from .Item import Item, Item
from .Map import Map
    
class Valids:
    """ Created per-Event to check to see if the Event will run in the Game. """
    
    def __init__(self, loadedMap: Map, loadedItems: list[Item]):
        self.charShorts: list[str] = []
        self.itemShorts: list[str] = []
        self.charTags: list[str] = []
        
        self.map = loadedMap
        self.loadedZoneNames = [zone.name for zone in loadedMap.zones]
        
        self.loadedItems = loadedItems
        self.loadedItemNames = [i.string() for i in self.loadedItems]
        self.loadedItemTags: set[str] = set()
        for item in self.loadedItems:
            for tag in item.tags:
                self.loadedItemTags.add(tag)
    
    def addCharShort(self, short: str):
        if self.isValidCharShort(short): return False
        self.charShorts.append(short)
        return True
    
    def addItemShort(self, short: str):
        if self.isValidItemShort(short): return False
        self.itemShorts.append(short)
        return True
    
    def addCharTag(self, name: str):
        if self.isValidCharTag(name): return False
        self.charTags.append(name)
        return True

    def isValidCharShort(self, short: str):
        return short in self.charShorts
    
    def isValidItemShort(self, short: str):
        return short in self.itemShorts
    
    def isValidCharTag(self, name: str):
        return name in self.charTags
    
    def isLoadedItem(self, name: str):
        return name in self.loadedItemNames
    
    def isLoadedItemTag(self, name: str):
        if name == "ANY":
            return True
        return name in self.loadedItemTags
    
    def isLoadedZone(self, name: str):
        return name in self.loadedZoneNames

    def getLoadedItemsWithTags(self, tags: list[str]):
        possItems = []
        for item in self.loadedItems:
            if item.hasAllTags(tags):
                possItems.append(item)
        return possItems
    
    def getLoadedItemWithName(self, name: str):
        # we've guaranteed the item name is valid when this is called
        for item in self.loadedItems:
            if item.string() == name:
                return [item]
    
    def getLoadedZoneWithName(self, name: str):
        for zone in self.map.zones:
            if zone.name == name:
                return zone

class EventPartException(Exception):
    """ Simple Exception for differentiating an Event's validation errors. """
    pass

class EventPart:
    args: list[str]
    matches: list[str]
    
    @classmethod
    def match(cls, args: list[str]) -> bool:
        """ Initially matches a list of args to this EventPart.
            Returns True if matched and False otherwise. """
        return any(args[0] == name for name in cls.matches)
    
    @classmethod
    def build(cls, args: list[str], valids: Valids):
        """ Gets an instance of thie EventPart, checking to see if the number of args match the expected number and erroring otherwise. """
        checkArgCount(args, cls.args)
        return cls(valids, *args)

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
def validateCharTag(name: str, valids: Valids):
    validate(valids.isValidCharTag, name, "tag name")
def validateLoadedItemTag(name: str, valids: Valids):
    validate(valids.isLoadedItemTag, name, "item tag")
def validateLoadedItemName(name: str, valids: Valids):
    validate(valids.isLoadedItem, name, "specific item name")
def validateLoadedZoneName(name: str, valids: Valids):
    validate(valids.isLoadedZone, name, "zone name")

def validate(fun: Callable, name: str, errName: str):
    if not fun(name):
        raise EventPartException(f"Encountered an invalid {errName}: `{name}`")

def validateIsInt(arg: str):
    for let in arg:
        if let not in "1234567890":
            raise EventPartException(f"{arg} is not a number, the expected argument is meant to be a number")

def addCharShortToValids(name: str, valids: Valids):
    addToValids(name, valids.addCharShort)
def addItemShortToValids(name: str, valids: Valids):
    addToValids(name, valids.addItemShort)
def addTagNameToValids(name: str, valids: Valids):
    addToValids(name, valids.addCharTag)

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
    def __init__(self, charShort: str, argsLists: list[list[str]]):
        self.charShort = charShort
        self.argsLists = argsLists
    
    def getCharShort(self):
        return self.charShort
    
    def load(self, valids: Valids, classes: list[Type[EventPart]], partsList: list[EventPart]):
        for args in self.argsLists:
            found = False
            for reqClass in classes:
                if reqClass.match(args):
                    try:
                        part = reqClass.build(args, valids)
                    except EventPartException as e:
                        raise self.exception(args, e)
                    partsList.append(part)
                    found = True
                    break
            if not found:
                raise self.exception(args, "Not recognized as a valid Effect")
        return valids
    
    def exception(self, args: list[str], e: Union[Exception, str]):
        argsStr = ""
        for arg in self.argsLists:
            if args == arg:
                argsStr += f"->"
            argsStr += " ".join(arg) + ", "
        argsStr = argsStr[:-2]
        return Exception(f"in line \"{self.charShort}: {argsStr}\"\n    {e}")
