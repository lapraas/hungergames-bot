
from __future__ import annotations
from abc import abstractmethod
from random import choice

from typing import Type, Union

from .Character import Character
from .Item import Item
from .State import State
from .Valids import EventPart, Suite, Valids

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
    args = ["type", "tag name"]
    matches = ["tag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, tag = args
        
        self.tag = tag
        valids.addCharTag(self.tag)
    
    def check(self, char: Character, state: State):
        return char.hasTag(self.tag)

class ItemCheck(Check):
    BY_TAGS = "item"
    BY_NAME = "itemeq"
    
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
        item: Item = None
        if self.rType == ItemCheck.BY_TAGS:
            item = char.getItemByTags(self.itemTags)
        else:
            item = char.getItemByName(self.itemTags[0])
        if not item: return False
        state.setItem(self.itemShort, item)
        return True

class CreateCheck(Check):
    BY_TAGS = "create"
    BY_NAME = "createeq"
    
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
    TOTAL = "total"
    PERCHAR = "perchar"
    
    args = ["type", "count type", "trigger count"]
    matches = ["limit"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.cType, self.count = args
        valids.validateIsNumber(self.count)
        self.count = int(self.count)
    
    def check(self, char: Character, state: State) -> bool:
        if self.cType == LimitCheck.PERCHAR:
            return state.getTriggersFor(char) <= self.count
        else:
            return state.getTotalTriggers() <= self.count

class TroveEmptyCheck(Check):
    args = ["type", "trove name"]
    matches = ["isempty"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.troveName = args
        valids.validateLoadedTroveName(self.troveName)
        self.trove = valids.getLoadedTroveWithName(self.troveName)
    
    def check(self, char: Character, state: State) -> bool:
        return self.trove.hasItems()

ALLCHECKCLASSES: list[Type[EventPart]] = [
    AliveCheck,
    AloneCheck,
    CreateCheck,
    DistanceCheck,
    ItemCheck,
    LimitCheck,
    LocationCheck,
    RelationCheck,
    TagCheck,
]

class CheckSuite(Suite):
    def __init__(self, charShort: str, argsLists: list[list[str]]):
        super().__init__(charShort, argsLists)
        
        self.checks: list[Check] = []
    
    def load(self, valids: Valids):
        valids.addCharShort(self.getCharShort())
        super().load(valids, ALLCHECKCLASSES, self.checks)
        if (not any([type(check) == AliveCheck for check in self.checks])):
            self.checks.insert(0, AliveCheck(valids, AliveCheck.ALIVE))
    
    def addNearbyCheckIfNeeded(self, valids: Valids):
        if (not any([type(check) == AliveCheck for check in self.checks])):
            self.checks.insert(0, DistanceCheck(valids, DistanceCheck.NEARBY))
    
    def checkAll(self, char: Character, state: State):
        allEffectTexts: list[str] = []
        for ep in self.checks:
            res = ep.check(char, state)
            allEffectTexts.append(res)
        return allEffectTexts
