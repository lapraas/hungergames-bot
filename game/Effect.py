
from __future__ import annotations
from abc import abstractmethod
from game.Item import Item
from game.Map import Map

from typing import Type, Union

from .Character import Character
from .State import State
from .Valids import EventPart, EventPartException, Suite, Valids, validateCharShort, validateItemShort, validateCharTag, validateLoadedZoneName

class Effect(EventPart):
    @abstractmethod
    def perform(self, char: Character, state: State) -> str:
        """ Performs the Effect on the Character.
            Returns a flavor string about what happened to the Character. """
        pass

class TagEffect(Effect):
    args = ["type", "tag name"]
    matches = ["tag"]
        
    def __init__(self, valids: Valids, *args: str):
        _, self.tag = args
    
    def perform(self, char: Character, state: State):
        char.addTag(self.tag)
        return f"added tag: {self.tag}"

class UntagEffect(Effect):
    args = ["type", "tag name"]
    matches = ["untag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.tag = args
        validateCharTag(self.tag, valids)
    
    def perform(self, char: Character, state: State):
        char.removeTag(self.tag)
        return f"removed tag: {self.tag}"

class ItemEffect(Effect):
    args = ["type", "item shorthand"]
    matches = ["give"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
    
    def perform(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.copyAndGiveItem(item)
        return f"gave item: {item}"

class AllyEffect(Effect):
    args = ["type", "char shorthand"]
    matches = ["ally"]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.charShort = args
        validateCharShort(self.charShort, valids)
    
    def perform(self, char: Character, state: State):
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

class LeaveEffect(Effect):
    args = ["type"]
    matches = ["leave"]
    
    def __init__(self, *_):
        pass
    
    def perform(self, char: Character, state: State):
        char.leaveAlliance()
        return "left alliance"

class ConsumeEffect(Effect):
    args = ["type", "item shorthand"]
    matches = ["consume"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
        validateItemShort(self.itemShort, valids)
    
    def perform(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.takeItem(item)
        return f"consumed item: {item}"

class MoveEffect(Effect):
    args = ["type", "zone name?"]
    matches = ["move"]
    
    def __init__(self, valids: Valids, *args: str):
        self.zone = None
        if len(args) >= 2:
            self.zone = args[1]
            validateLoadedZoneName(self.zone, valids)
            self.zone = valids.getLoadedZoneWithName(self.zone)
    
    def perform(self, char: Character, state: State):
        if self.zone:
            char.move(self.zone)
        else:
            char.moveRandom()
        return f"moved to zone: {char.getLocation().name}"

class KillEffect(Effect):
    args = ["type"]
    matches = ["kill"]
    
    def __init__(self, valids: Valids, *args: str):
        pass
    
    def perform(self, char: Character, state: State):
        char.kill()
        return f"killed: {char.string()}"

class ReviveEffect(Effect):
    args = ["type"]
    matches = ["revive"]
    
    def __init__(self, valids: Valids, *args: str):
        pass
    
    def perform(self, char: Character, state: State):
        char.revive()
        return f"revived: {char.string()}"

ALLEFFECTCLASSES: list[Type[EventPart]] = [
    TagEffect,
    UntagEffect,
    ItemEffect,
    AllyEffect,
    LeaveEffect,
    ConsumeEffect,
    MoveEffect,
    KillEffect,
    ReviveEffect
]

class EffectSuite(Suite):
    def __init__(self, charShort: str, argsLists: list[list[str]]):
        super().__init__(charShort, argsLists)
        self.effects: list[Effect] = []
    
    def load(self, valids: Valids):
        super().load(valids, ALLEFFECTCLASSES, self.effects)
    
    def performAll(self, char: Character, state: State):
        allEffectTexts: list[str] = []
        for ep in self.effects:
            res = ep.perform(char, state)
            allEffectTexts.append(res)
        return allEffectTexts
