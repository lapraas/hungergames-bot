
from __future__ import annotations
from abc import abstractmethod
from random import choice

from typing import Type, Union

from game.Character import Character
from game.Item import Item
from game.State import State
from game.Valids import EventPart, Suite, Valids

class Check(EventPart):
    @abstractmethod
    def check(self, char: Character, state: State) -> bool:
        """ Checks to see if the Character meets this Check.
            Returns True if so, False otherwise. """
        pass

class DistanceCheck(Check):
    NEARBY = "nearby"
    ANYDISTANCE = "anydistance"
    
    args = ["char short?"]
    matches = [NEARBY, ANYDISTANCE]
    
    def __init__(self, valids: Valids, *args: str):
        self.state, self.targetShort = args
    
    def check(self, char: Character, state: State) -> bool:
        if self.state == DistanceCheck.NEARBY:
            target = state.getChar(self.targetShort)
            return char.isNearby(target)
        else:
            return True

class AliveCheck(Check):
    ALIVE = "alive"
    DEAD = "dead"
    
    args = []
    matches = [ALIVE, DEAD]
    
    def __init__(self, valids: Valids, *args: str):
        self.aState, = args
    
    def check(self, char: Character, state: State) -> bool:
        if self.aState == AliveCheck.ALIVE:
            return char.isAlive()
        else:
            return not char.isAlive()

class AloneCheck(Check):
    ALONE = "alone"
    ALLIED = "allied"
    
    args = []
    matches = [ALONE, ALLIED]

    def __init__(self, valids: Valids, *args: str):
        self.state, = args
    
    def check(self, char: Character, state: State) -> bool:
        if self.state == AloneCheck.ALONE and char.isAlone():
            return True
        if self.state == AloneCheck.ALLIED and not char.isAlone():
            return True
        return False

class RelationCheck(Check):
    ALLY = "ally"
    ENEMY = "enemy"
    
    args = ["char short"]
    matches = [ALLY, ENEMY]
        
    def __init__(self, valids: Valids, *args: str):
        self.relationship, self.targetShort = args
    
    def check(self, char: Character, state: State):
        target = state.getChar(self.targetShort)
        
        if self.relationship == RelationCheck.ALLY and char.isAllyOf(target):
            return True
        if self.relationship == RelationCheck.ENEMY and not char.isAllyOf(target):
            return True
        return False

class ComparisonCheck(Check):
    args = ["comparison", "number"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.comp, self.number = args

    def getVal(self, char: Character) -> int:
        pass
    
    def check(self, char: Character, state: State) -> bool:
        if self.comp == "=":
            return self.number == self.getVal(char)
        if self.comp == "!":
            return self.number != self.getVal(char)
        if self.comp == "<":
            return self.getVal(char) < self.number
        if self.comp == ">":
            return self.getVal(char) > self.number

class RoundCheck(ComparisonCheck):
    matches = ["round"]
    
    def getVal(self, char: Character) -> int:
        return char.getAge()

class StatusCheck(ComparisonCheck):
    args = ["any", "comparison?", "number?"]
    matches = ["status"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.status, self.comp, self.number = args
        if not self.comp:
            self.comp = ">"
        if not self.number:
            self.number = 0
    
    def getVal(self, char: Character) -> int:
        return char.getStatusAge()
    
    def check(self, char: Character, state: State) -> bool:
        if not char.hasStatus(self.status): return False
        super().check(char, state)

class TagCheck(ComparisonCheck):
    args = ["new char tag", "comparison?", "number?"]
    matches = ["tag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.tag, self.comp, self.age = args
        self.flip = self.tag.startswith("!")
        
        if self.flip: self.tag = self.tag[1:]
    
    def getVal(self, char: Character) -> int:
        return char.getTagAge(self.tag)
    
    def check(self, char: Character, state: State) -> bool:
        if not char.hasTag(self.tag): return True if self.flip else False
        res = super().check(char, state)
        return (not res) if self.flip else res

class ItemCheck(Check):
    args = ["new item short", "*item tag"]
    matches = ["item"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, *itemTags = args
        self.itemTags = itemTags
    
    def get(self, char: Character):
        return char.getItemByTags(self.itemTags)
    
    def check(self, char: Character, state: State) -> bool:
        item = self.get(char)
        if not item: return False
        state.setItem(self.itemShort, item)
        return True

class ItemNamedCheck(ItemCheck):
    args = ["new item short", "item name"]
    matches = ["itemnamed"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, self.itemName = args
    
    def get(self, char: Character):
        return char.getItemByName(self.itemName)

class NeedsCheck(Check):
    args = ["*item tag"]
    matches = ["needs"]
    
    def __init__(self, valids: Valids, *args: str):
        _, *itemTags = args
        self.itemTags = itemTags
    
    def check(self, char: Character, state: State) -> bool:
        return char.getItemByTags(self.itemTags) == False

class CreateCheck(Check):
    args = ["new item short", "*item tag"]
    matches = ["create"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, *itemTags = args
        self.itemTags = itemTags
        
        self.items: list[Item] = valids.getLoadedItemsWithTags(self.itemTags)
    
    def check(self, char: Character, state: State) -> bool:
        item = choice(self.items)
        state.setItem(self.itemShort, item)
        return True

class CreateNamedCheck(CreateCheck):
    args = ["new item short", "item name"]
    matches = ["createnamed"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, self.itemName = args
        self.items = [valids.getLoadedItemWithName(self.itemName)]

class LocationCheck(Check):
    args = ["zone name"]
    matches = ["in"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.locName = args
    
    def check(self, char: Character, state: State) -> bool:
        return char.isIn(self.locName)

class LimitCheck(Check):
    TOTAL = "limittotal"
    PERCHAR = "limit"
    
    args = ["number"]
    matches = [PERCHAR, TOTAL]
    
    def __init__(self, valids: Valids, *args: str):
        self.cType, self.count = args
    
    def check(self, char: Character, state: State) -> bool:
        if self.cType == LimitCheck.PERCHAR:
            return state.getTriggersFor(char) <= self.count
        else:
            return state.getTotalTriggers() <= self.count

class TroveCheck(Check):
    args = ["new item short", "trove name"]
    matches = ["loot"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.newItemShort, troveName = args
        self.trove = valids.getLoadedTroveWithName(troveName)
    
    def check(self, char: Character, state: State) -> bool:
        if not self.trove.hasItems():
            return False
        state.setItem(self.newItemShort, self.trove.loot())
        return True

class AddChanceCheck(Check):
    args = ["number?"]
    matches = ["luck"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.number = args
        if not self.number: self.number = 1
    
    def check(self, char: Character, state: State) -> bool:
        state.addChances(self.number)
        return True

ALLCHECKCLASSES: list[Type[EventPart]] = [
    AddChanceCheck,
    AliveCheck,
    AloneCheck,
    CreateCheck,
    CreateNamedCheck,
    DistanceCheck,
    ItemCheck,
    ItemNamedCheck,
    LimitCheck,
    LocationCheck,
    NeedsCheck,
    RelationCheck,
    RoundCheck,
    StatusCheck,
    TagCheck,
    TroveCheck
]

class CheckSuite(Suite):
    def __init__(self, charShort: str, argsLists: list[list[str]]):
        super().__init__(charShort, argsLists)
        
        self.checks: list[Check] = []
        self.isSubEvent: bool = False
    
    def load(self, valids: Valids, isSubEvent: bool=False):
        self.checks = []
        valids.addCharShort(self.getCharShort())
        super().load(valids, ALLCHECKCLASSES, self.checks)
        
        self.isSubEvent = isSubEvent
        if not self.isSubEvent:
            if (not any([type(check) == AliveCheck for check in self.checks])):
                self.checks.insert(0, AliveCheck(valids, AliveCheck.ALIVE))
            if (not any([type(check) == RoundCheck for check in self.checks])):
                self.checks.insert(0, RoundCheck(valids, None, "!", 1))
    
    def addNearbyCheckIfNeeded(self, valids: Valids):
        if (not any([type(check) == AliveCheck for check in self.checks])):
            self.checks.insert(0, DistanceCheck(valids, DistanceCheck.NEARBY, None))
    
    def checkAll(self, char: Character, state: State):
        if char.status and not self.isSubEvent:
            checked = False
            for check in self.checks:
                if type(check) == StatusCheck:
                    if not check.check(char, state): return False
                    checked = True
            if not checked: return False
        for check in self.checks:
            res = check.check(char, state)
            if not res: return False
        return True
