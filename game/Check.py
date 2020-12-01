
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

class TagCheck(Check):
    NONE = "tag"
    EQ = "tag="
    LT = "tag<"
    GT = "tag>"
    
    args = ["new char tag", "number?"]
    matches = [NONE, EQ, LT, GT]
    
    def __init__(self, valids: Valids, *args: str):
        self.tType, self.tag, self.age = args
        
        self.flip = self.tag.startswith("!")
        if self.flip: self.tag = self.tag[1:]
    
    def check(self, char: Character, state: State):
        if self.tType in [TagCheck.NONE, TagCheck.GT]:
            toRet = char.getTagAge(self.tag) > self.age
        if self.tType == TagCheck.EQ:
            toRet = char.getTagAge(self.tag) == self.age
        else:
            toRet = char.getTagAge(self.tag) < self.age
        return toRet if not self.flip else not toRet

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

class CreateCheck(Check):
    args = ["new item short", "*item tag"]
    matches = ["create"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, *itemTags = args
        self.itemTags = itemTags
        
        items: list[Item] = valids.getLoadedItemsWithTags(self.itemTags)
        self.item = choice(items)
    
    def check(self, char: Character, state: State) -> bool:
        state.setItem(self.itemShort, self.item)
        return True

class CreateNamedCheck(CreateCheck):
    args = ["new item short", "item name"]
    matches = ["createnamed"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort, self.itemName = args
        self.item = valids.getLoadedItemWithName(self.itemName)

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

class RoundCheck(Check):
    args = ["comparison", "number"]
    matches = ["round"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.comp, self.number = args
    
    def getVal(self, char: Character) -> int:
        return char.getAge()
    
    def check(self, char: Character, state: State) -> bool:
        if self.comp == "=":
            return self.number == self.getVal(char)
        if self.comp == "!":
            return self.number != self.getVal(char)
        if self.comp == "<":
            return self.getVal(char) < self.number
        if self.comp == ">":
            return self.getVal(char) > self.number

class StatusCheck(RoundCheck):
    args = ["comparison", "number"]
    matches = ["status"]
    
    def getVal(self, char: Character) -> int:
        return char.getStatusAge()

ALLCHECKCLASSES: list[Type[EventPart]] = [
    AliveCheck,
    AloneCheck,
    CreateCheck,
    CreateNamedCheck,
    DistanceCheck,
    ItemCheck,
    ItemNamedCheck,
    LimitCheck,
    LocationCheck,
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
    
    def load(self, valids: Valids, isSub: bool=False):
        self.checks = []
        valids.addCharShort(self.getCharShort())
        super().load(valids, ALLCHECKCLASSES, self.checks)
        if not isSub:
            if (not any([type(check) == AliveCheck for check in self.checks])):
                self.checks.insert(0, AliveCheck(valids, AliveCheck.ALIVE))
            if (not any([type(check) == RoundCheck for check in self.checks])):
                self.checks.insert(0, RoundCheck(valids, None, "!", 1))
    
    def addNearbyCheckIfNeeded(self, valids: Valids):
        if (not any([type(check) == AliveCheck for check in self.checks])):
            self.checks.insert(0, DistanceCheck(valids, DistanceCheck.NEARBY))
    
    def checkAll(self, char: Character, state: State):
        for check in self.checks:
            res = check.check(char, state)
            if not res: return False
        return True
