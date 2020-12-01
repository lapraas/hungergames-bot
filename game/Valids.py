
from __future__ import annotations
from game.Trove import Trove

import re
from typing import Callable, Type, Union

from game.Item import Item, Item
from game.Map import Map, Zone

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
        
        self.checks = {
            "char short": self.validateCharShort,
            "item short": self.validateItemShort,
            "char tag": self.validateCharTag,
            "item name": self.validateLoadedItemName,
            "item tag": self.validateLoadedItemTag,
            "zone name": self.validateLoadedZoneName,
            "trove name": self.validateLoadedTroveName,
            "number": self.validateIsNumber,
            "comparison": self.validateIsComparison,
            "new item short": self.addItemShort,
            "new char short": self.addCharShort,
            "new char tag": self.addCharTag
        }
    
    #
    #
    # Adding shorts and tags
    #
    #
    
    def addCharShort(self, short: str):
        self.charShorts.append(short)
    
    def addItemShort(self, short: str):
        self.itemShorts.append(short)
    
    def addCharTag(self, name: str):
        if name.startswith("!"): name = name[1:]
        if name in self.charTags: return
        self.charTags.append(name)

    #
    #
    # Checking shorts and tags
    #
    #

    def validateCharShort(self, short: str):
        if not short in self.charShorts:
            raise ValidationException(f"Encountered an invalid Character shorthand: \"{short}\"")
    
    def validateItemShort(self, short: str):
        if not short in self.itemShorts:
            raise ValidationException(f"Encountered an invalid Item shorthand: \"{short}\"")
    
    def validateCharTag(self, name: str):
        if name.startswith("!"): name = name[1:]
        if not name in self.charTags:
            raise ValidationException(f"Encountered an invalid Character tag: \"{name}\"")
    
    def validateLoadedItemTag(self, name: str):
        if name == "ANY" or name == "SECRET": return
        if name.startswith("!"): name = name[1:]
        if not name in self.loadedItemTags:
            raise ValidationException(f"Encountered an invalid Item tag: \"{name}\"")
    
    def validateLoadedItemName(self, args: list[str]):
        name = " ".join(args)
        if not name in self.loadedItems:
            raise ValidationException(f"Encountered an invalid Item name (is it loaded?): \"{name}\"")
        return name
    
    def validateLoadedZoneName(self, args: list[str]):
        name = " ".join(args)
        if not name in self.map.zones:
            raise ValidationException(f"Encountered an invalid Zone name: \"{name}\"")
        return name
    
    def validateLoadedTroveName(self, args: list[str]):
        name = " ".join(args)
        if not name in self.map.troves:
            raise ValidationException(f"Encountered an invalid Trove name: \"{name}\"")
        return name
    
    #
    #
    # Type checks
    #
    #
    
    def validateIsNumber(self, arg):
        for let in arg:
            if let not in "1234567890-":
                raise ValidationException(f"Encountered an invalid argument, expceted number: \"{arg}\"")
        return int(arg)
    
    def validateIsComparison(self, arg):
        comparisons = "=!<>"
        if not arg in comparisons:
            raise ValidationException(f"Encountered an invalid argument, expeged comparison ({comparisons}): \"{arg}\"")
        return arg

    #
    #
    # Getters for selections
    #
    #
    
    def getLoadedItemsWithTags(self, tags: list[str]) -> list[Item]:
        possItems = []
        for item in self.loadedItems.values():
            if item.hasAllTags(tags):
                possItems.append(item)
        return possItems
    
    def getLoadedItemWithName(self, name: str) -> Item:
        # we've guaranteed the item name is valid when this is called
        return self.loadedItems.get(name)
    
    def getLoadedZoneWithName(self, name: str) -> Zone:
        return self.map.getZone(name)
    
    def getLoadedTroveWithName(self, name: str) -> Trove:
        return self.map.getTrove(name)
    
    def validateArgs(self, types: list[str], args: list[str]) -> None:
        i = 0
        #print("Validating")
        #print(f"  types: {types}")
        #print(f"  args:  {args}")
        while i < len(types):
            typ = types[i]
            #print(f"    typ: {typ}")
            
            if i >= len(args):
                args.append(None)
            arg = args[i]
            #print(f"    arg: {arg}")
            
            if typ == "any": # Matches any
                i += 1
                continue
            
            if typ.endswith("?"): # Nullable argument
                typ = typ[:-1]
                if arg == None:
                    i += 1
                    continue
            
            if typ.endswith("name"): # hello future me when this doesn't work smile
                arg = args[i:]
                args = args[:i+1]
            if typ.startswith("*"): # Check the rest of the arguments against the current type
                typ = typ[1:]
                while len(types) < len(args):
                    types.append(typ)
            
            typeFun = self.checks.get(typ)
            if not typeFun: raise Exception(f"Couldn't find method for validating arg of type {typ}")
            
            cast = typeFun(arg)
            if cast != None: args[i] = cast
            
            i += 1
        #print("Finished\n")
    
    #
    #
    # Text validation
    #
    #
    
    def validateText(self, text) -> None:
        textReplacePat = re.compile(r"([A-Za-z'\\]*)(@|&)(\w+)")
        matches = textReplacePat.finditer(text)
        for match in matches:
            tag, objType, short = match.groups()
            if tag.endswith("\\"): continue
            if objType == "&":
                if tag != "" and not tag.lower() == "a":
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered non-article conjugation for {tag}&{short}")
                if not short in self.itemShorts:
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered invalid Item shorthand: \"{tag}&{short}\"")
            elif objType == "@":
                if not short in self.charShorts:
                    raise ValidationException(f"in text:\n    \"{text}\"\n    Encountered invalid Character shorthand: \"{tag}@{short}\"")

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
        """ Gets an instance of this EventPart, checking to see if the number of args match the expected number and erroring otherwise. """
        ct = len(cls.args)
        if not ct:
            return cls(valids, *args)
            
        toCheck = args[1:]
        
        argsStr = ", ".join(cls.args)
        minCt = ct
        while cls.args[minCt - 1].endswith("?"):
            minCt -= 1
            if minCt - 1 < 0:
                break
            
        
        if cls.args[-1].startswith("*"):
            if len(toCheck) < ct:
                raise ValidationException(f"Needs {minCt} or more arguments ({len(toCheck)} recieved): {argsStr}")
        else:
            if minCt == ct:
                if len(toCheck) != ct:
                    raise ValidationException(f"Needs {ct} arguments ({len(toCheck)} recieved): {argsStr}")
            elif len(toCheck) < minCt or len(toCheck) > ct:
                raise ValidationException(f"Needs {minCt}-{ct} arguments ({len(toCheck)} recieved): {argsStr}")
        
        valids.validateArgs(cls.args, toCheck)
        return cls(valids, *[args[0], *toCheck])
    
    def __init__(self, valids: Valids, *args: Union[str, int]):
        pass

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
