
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
    
    args = ["nearby state (type)", "target char shorthand?"]
    matches = [NEARBY, ANYDISTANCE]
    
    def __init__(self, valids: Valids, *args: str):
        if len(args) == 2 and args[0] == DistanceCheck.NEARBY:
            self.state, self.targetShort = args
            valids.validateCharShort(self.targetShort)
        else:
            self.state, = args
            self.targetShort = None
    
    def check(self, char: Character, state: State) -> bool:
        if self.state == DistanceCheck.NEARBY:
            target = state.getChar(self.targetShort)
            return char.isNearby(target)
        else:
            return True

class AliveCheck(Check):
    ALIVE = "alive"
    DEAD = "dead"
    
    args = ["alive state (type)"]
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
    
    args = ["type"]
    matches = [ALONE, ALLIED]

    def __init__(self, valids: Valids, *args: str):
        state, = args
        
        self.state = state
    
    def check(self, char: Character, state: State) -> bool:
        if self.state == AloneCheck.ALONE and char.isAlone():
            return True
        if self.state == AloneCheck.ALLIED and not char.isAlone():
            return True
        return False

class RelationCheck(Check):
    ALLY = "ally"
    ENEMY = "enemy"
    
    args = ["relationship (type)", "target char shorthand"]
    matches = [ALLY, ENEMY]
        
    def __init__(self, valids: Valids, *args: str):
        relationship, targetShort = args
        valids.validateCharShort(targetShort)
        
        self.relationship = relationship
        self.targetShort = targetShort
    
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
    
    args = ["tag check type", "tag name", "tag time?"]
    matches = [NONE, EQ, LT, GT]
    
    def __init__(self, valids: Valids, *args: str):
        self.tType, self.tag = args[:2]
        self.age = "-1" if not len(args) > 3 else args[2]
        
        self.flip = self.tag.startswith("!")
        if self.flip: self.tag = self.tag[1:]
        
        valids.validateIsNumber(self.age)
        self.age = int(self.age)
        valids.addCharTag(self.tag)
    
    def check(self, char: Character, state: State):
        if self.tType in [TagCheck.NONE, TagCheck.GT]:
            toRet = char.getTagAge(self.tag) > self.age
        if self.tType == TagCheck.EQ:
            toRet = char.getTagAge(self.tag) == self.age
        else:
            toRet = char.getTagAge(self.tag) < self.age
        return toRet if not self.flip else not toRet

class ItemCheck(Check):
    BY_TAGS = "item"
    BY_NAME = "item="
    
    args = ["type", "item shorthand", "*item tags"]
    matches = [BY_TAGS, BY_NAME]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.itemShort, *itemTags = args
        self.itemTags = itemTags
        
        valids.addItemShort(self.itemShort)
        
        if self.rType == ItemCheck.BY_TAGS:
            for tag in self.itemTags:
                valids.validateLoadedItemTag(tag)
    
    def check(self, char: Character, state: State) -> bool:
        if self.rType == ItemCheck.BY_TAGS:
            item = char.getItemByTags(self.itemTags)
        else:
            item = char.getItemByName(self.itemTags[0])
        if not item: return False
        state.setItem(self.itemShort, item)
        return True

class CreateCheck(Check):
    BY_TAGS = "create"
    BY_NAME = "create="
    
    args = ["type", "item shorthand", "*item tags"]
    matches = [BY_TAGS, BY_NAME]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.itemShort, *itemTags = args
        self.itemTags = itemTags
        
        self.items: list[Item] = None
        valids.addItemShort(self.itemShort)
        
        if self.rType == CreateCheck.BY_TAGS:
            for tag in self.itemTags:
                valids.validateLoadedItemTag(tag)
        
        if self.rType == CreateCheck.BY_TAGS:
            self.items = valids.getLoadedItemsWithTags(self.itemTags)
        else:
            self.items = valids.getLoadedItemWithName(self.itemTags[0])
    
    def check(self, char: Character, state: State) -> bool:
        item = choice(self.items)
        state.setItem(self.itemShort, item)
        return True

class LocationCheck(Check):
    args = ["type", "location name"]
    matches = ["in"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.locName = args
        
        valids.validateLoadedZoneName(self.locName)
    
    def check(self, char: Character, state: State) -> bool:
        return char.isIn(self.locName)

class LimitCheck(Check):
    TOTAL = "limittotal"
    PERCHAR = "limit"
    
    args = ["count type", "trigger count"]
    matches = [PERCHAR, TOTAL]
    
    def __init__(self, valids: Valids, *args: str):
        self.cType, self.count = args
        valids.validateIsNumber(self.count)
        self.count = int(self.count)
    
    def check(self, char: Character, state: State) -> bool:
        if self.cType == LimitCheck.PERCHAR:
            return state.getTriggersFor(char) <= self.count
        else:
            return state.getTotalTriggers() <= self.count

class TroveCheck(Check):
    args = ["type", "trove name", "item short"]
    matches = ["takefrom"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.troveName, self.newItemShort = args
        valids.validateLoadedTroveName(self.troveName)
        self.trove = valids.getLoadedTroveWithName(self.troveName)
        valids.addItemShort(self.newItemShort)
    
    def check(self, char: Character, state: State) -> bool:
        if not self.trove.hasItems():
            return False
        state.setItem(self.newItemShort, self.trove.loot())
        return True

class RoundCheck(Check):
    EQUAL = "round="
    NOTEQUAL = "round!="
    BEFORE = "round<"
    AFTER = "round>"
    
    args = ["round comparison", "number"]
    matches = [EQUAL, NOTEQUAL, BEFORE, AFTER]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.number = args
        valids.validateIsNumber(self.number)
        self.number = int(self.number)
    
    def check(self, char: Character, state: State) -> bool:
        if self.rType == RoundCheck.EQUAL:
            return self.number == char.getAge()
        if self.rType == RoundCheck.NOTEQUAL:
            return self.number != char.getAge()
        if self.rType == RoundCheck.BEFORE:
            return char.getAge() < self.number
        if self.rType == RoundCheck.AFTER:
            return char.getAge() > self.number

ALLCHECKCLASSES: list[Type[EventPart]] = [
    AliveCheck,
    AloneCheck,
    CreateCheck,
    DistanceCheck,
    ItemCheck,
    LimitCheck,
    LocationCheck,
    RelationCheck,
    RoundCheck,
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
                self.checks.insert(0, RoundCheck(valids, RoundCheck.NOTEQUAL, "1"))
    
    def addNearbyCheckIfNeeded(self, valids: Valids):
        if (not any([type(check) == AliveCheck for check in self.checks])):
            self.checks.insert(0, DistanceCheck(valids, DistanceCheck.NEARBY))
    
    def checkAll(self, char: Character, state: State):
        for check in self.checks:
            res = check.check(char, state)
            if not res: return False
        return True
