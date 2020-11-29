
from __future__ import annotations

import re
from typing import Callable, Type, Union

from .Item import Item, Item
from .Map import Map
    
class Valids:
    """ Created per-Event to check to see if the Event will run in the Game. """
    
    def __init__(self, loadedMap: Map, loadedItems: dict[str, Item]):
        self.charShorts: list[str] = []
        self.itemShorts: list[str] = []
        self.charTags: list[str] = []
        
        self.map = loadedMap
        
        self.loadedItems = loadedItems
        self.loadedItemTags: set[str] = set()
        for item in self.loadedItems.values():
            for tag in item.tags:
                self.loadedItemTags.add(tag)
    
    def addCharShort(self, short: str):
        self.charShorts.append(short)
    
    def addItemShort(self, short: str):
        if short in self.itemShorts: raise ValidationException(f"Encountered a duplicate Item shorthand: \"{short}\"")
        self.itemShorts.append(short)
    
    def addCharTag(self, name: str):
        if name in self.charTags: return
        self.charTags.append(name)

    def validateCharShort(self, short: str):
        if not short in self.charShorts:
            raise ValidationException(f"Encountered an invalid Character shorthand: \"{short}\"")
    
    def validateItemShort(self, short: str):
        if not short in self.itemShorts:
            raise ValidationException(f"Encountered an invalid Item shorthand: \"{short}\"")
    
    def validateCharTag(self, name: str):
        if not name in self.charTags:
            raise ValidationException(f"Encountered an invalid Character tag: \"{name}\"")
    
    def validateLoadedItem(self, name: str):
        if not name in self.loadedItems:
            raise ValidationException(f"Encountered an invalid Item name (is it loaded?): \"{name}\"")
    
    def validateLoadedItemTag(self, name: str):
        if name == "ANY" or name == "SECRET": return
        if not name in self.loadedItemTags:
            raise ValidationException(f"Encountered an invalid Item tag: \"{name}\"")
    
    def validateLoadedZoneName(self, name: str):
        if not name in self.map.zones:
            raise ValidationException(f"Encountered an invalid Zone name: \"{name}\"")
    
    def validateLoadedTroveName(self, name: str):
        if not name in self.map.troves:
            raise ValidationException(f"Encountered an invalid Trove name: \"{name}\"")
    
    def validateIsNumber(self, arg):
        for let in arg:
            if let not in "1234567890":
                raise ValidationException(f"Encountered an invalid argument, expceted number: \"{arg}\"")
    
    def validateText(self, text):
        textReplacePat = re.compile(r"([A-Za-z']*)(@|&)(\w+)")
        matches = textReplacePat.finditer(text)
        for match in matches:
            tag, objType, short = match.groups()
            if objType == "&":
                if tag != "" and not tag.lower() == "a":
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered non-article conjugation for {tag}&{short}")
                if not short in self.itemShorts:
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered invalid Item shorthand: \"{tag}&{short}\"")
            elif objType == "@":
                if not short in self.charShorts:
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered invalid Character shorthand: \"{tag}@{short}\"")

    def getLoadedItemsWithTags(self, tags: list[str]):
        possItems = []
        for item in self.loadedItems.values():
            if item.hasAllTags(tags):
                possItems.append(item)
        return possItems
    
    def getLoadedItemWithName(self, name: str):
        # we've guaranteed the item name is valid when this is called
        return self.loadedItems.get(name)
    
    def getLoadedZoneWithName(self, name: str):
        return self.map.getZone(name)
    
    def getLoadedTroveWithName(self, name: str):
        return self.map.getTrove(name)

class ValidationException(Exception):
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
                raise ValidationException(f"Needs {ct - 1} or {ct} arguments ({len(args)} recieved): {argsStr}")
        else:
            if len(args) != ct:
                raise ValidationException(f"Needs {ct} arguments ({len(args)} recieved): {argsStr}")
    else:
        if argNames[-1].endswith("?"):
            ct -= 1
        if len(args) < ct:
            raise ValidationException(f"Needs {ct} or more arguments ({len(args)} recieved): {argsStr}")

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
                    except ValidationException as e:
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
        return ValidationException(f"in line \"{self.charShort}: {argsStr}\"\n    {e}")
