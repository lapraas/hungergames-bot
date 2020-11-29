
from __future__ import annotations
from abc import abstractmethod
from game.Item import Item
from game.Map import Map

from typing import Type, Union

from .Character import Character
from .State import State
from .Valids import EventPart, Suite, Valids
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
        valids.validateCharTag(self.tag)
    
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
        valids.validateCharShort(self.charShort)
    
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
        valids.validateItemShort(self.itemShort)
    
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
            valids.validateLoadedZoneName(self.zone)
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
    AllyEffect,
    ConsumeEffect,
    ItemEffect,
    KillEffect,
    LeaveEffect,
    MoveEffect,
    ReviveEffect,
    TagEffect,
    UntagEffect
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
