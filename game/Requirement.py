
from __future__ import annotations
from random import choice

from typing import Type

from game.Character import Character
from game.Item import Item, Item
from game.State import State
from game.Valids import EventPart, Valids, addItemShortToValids, addTagNameToValids, validateCharShort, validateItemTag, validateZoneName

class AloneReq(EventPart):
    ALONE = "alone"
    ALLIED = "allied"
    
    args = ["type"]
    matches = [ALONE, ALLIED]

    def __init__(self, _, *args: str):
        state, = args
        
        self.state = state
    
    def do(self, char: Character, state: State) -> bool:
        if self.state == "alone" and char.isAlone():
            return True
        if self.state == "allied" and not char.isAlone():
            return True
        return False

class RelationReq(EventPart):
    ALLY = "ally"
    ENEMY = "enemy"
    
    args = ["relationship (type)", "target char shorthand"]
    matches = [ALLY, ENEMY]
        
    def __init__(self, valids: Valids, *args: str):
        relationship, targetShort = args
        validateCharShort(targetShort, valids)
        
        self.relationship = relationship
        self.targetShort = targetShort
    
    def do(self, char: Character, state: State):
        target = state.getChar(self.targetShort)
        
        if self.relationship == RelationReq.ALLY and char.isAllyOf(target):
            return True
        if self.relationship == RelationReq.ENEMY and not char.isAllyOf(target):
            return True
        return False

class TagReq(EventPart):
    args = ["type", "tag name"]
    matches = ["tag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, tag = args
        
        self.tag = tag
        addTagNameToValids(self.tag, valids)
    
    def do(self, char: Character, state: State):
        return char.hasTag(self.tag)

class ItemReq(EventPart):
    BY_TAGS = "item"
    BY_NAME = "itemeq"
    
    args = ["type", "item shorthand", "*item tags"]
    matches = [BY_TAGS, BY_NAME]
    
    def __init__(self, valids: Valids, *args: str):
        rType, itemShort, *itemTags = args
        if rType == ItemReq.BY_TAGS:
            for tag in itemTags:
                validateItemTag(tag, valids)
        
        self.rType = rType
        self.itemShort = itemShort
        self.itemTags = itemTags
        
        addItemShortToValids(self.itemShort, valids)
    
    def do(self, char: Character, state: State) -> bool:
        item: Item = None
        if self.rType == ItemReq.BY_TAGS:
            item = char.getItemByTags(self.itemTags)
        else:
            item = char.getItemByName(self.itemTags[0])
        if not item: return False
        state.setItem(self.itemShort, item)
        return True

class CreateReq(EventPart):
    BY_TAGS = "create"
    BY_NAME = "createeq"
    
    args = ["type", "item shorthand", "*item tags"]
    matches = [BY_TAGS, BY_NAME]
    
    def __init__(self, valids: Valids, *args: str):
        rType, itemShort, *itemTags = args
        if rType == CreateReq.BY_TAGS:
            for tag in itemTags:
                validateItemTag(tag, valids)
        
        self.itemShort = itemShort
        self.itemTags = itemTags
        
        self.items: list[Item] = None
        if rType == CreateReq.BY_TAGS:
            self.items = valids.getAllItemsWithTags(self.itemTags)
        else:
            self.items = valids.getItemWithName(self.itemTags[0])
        addItemShortToValids(self.itemShort, valids)
    
    def do(self, char: Character, state: State) -> bool:
        item = choice(self.items)
        state.setItem(self.itemShort, item)
        return True

class LocationReq(EventPart):
    args = ["type", "location name"]
    matches = ["in"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.locName = args
        
        validateZoneName(self.locName, valids)
    
    def do(self, char: Character, state: State) -> bool:
        return char.isIn(self.locName)

ALLREQCLASSES: list[Type[EventPart]] = [
    AloneReq,
    RelationReq,
    TagReq,
    ItemReq,
    CreateReq,
    LocationReq
]
