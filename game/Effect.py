
from __future__ import annotations
from abc import abstractmethod

from typing import Type

from game.Character import Character, Tag
from game.State import State
from game.Valids import EventPart, Suite, Valids

class Effect(EventPart):
    @abstractmethod
    def perform(self, char: Character, state: State) -> str:
        """ Performs the Effect on the Character.
            Returns a flavor string about what happened to the Character. """
        pass

class TagEffect(Effect):
    args = ["any", "number?"]
    matches = ["tag"]
        
    def __init__(self, valids: Valids, *args: str):
        _, self.tag, self.tagAge = args
    
    def perform(self, char: Character, state: State):
        char.addTag(self.tag, self.tagAge)
        return f"added tag: {self.tag}"

class UntagEffect(Effect):
    args = ["char tag"]
    matches = ["untag"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.tag = args
    
    def perform(self, char: Character, state: State):
        char.removeTag(self.tag)
        return f"removed tag: {self.tag}"

class StatusEffect(Effect):
    args = ["any"]
    matches = ["status"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.status = args
    
    def perform(self, char: Character, state: State) -> str:
        char.makeStatus(self.status)
        return f"set status: {self.status}"

class ClearEffect(Effect):
    args = []
    matches = ["clear"]
    
    def perform(self, char: Character, state: State) -> str:
        char.clearStatus()
        return "cleared status"

class ItemEffect(Effect):
    args = ["item short"]
    matches = ["give"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
    
    def perform(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.copyAndGiveItem(item)
        return f"gave item: {item}"

class AllyEffect(Effect):
    args = ["char short"]
    matches = ["ally"]
    
    def __init__(self, valids: Valids, *args: str):
        self.rType, self.charShort = args
    
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
            return f"joined alliance of: {toAlly}"

class LeaveEffect(Effect):
    args = []
    matches = ["leave"]
    
    def perform(self, char: Character, state: State):
        char.leaveAlliance()
        return "left alliance"

class ConsumeEffect(Effect):
    args = ["item short"]
    matches = ["consume"]
    
    def __init__(self, valids: Valids, *args: str):
        _, self.itemShort = args
    
    def perform(self, char: Character, state: State):
        item = state.getItem(self.itemShort)
        char.takeItem(item)
        return f"consumed item: {item}"

class MoveEffect(Effect):
    args = ["zone name?"]
    matches = ["move"]
    
    def __init__(self, valids: Valids, *args: str):
        _, zoneName, = args
        self.zone = None
        if zoneName:
            self.zone = valids.getLoadedZoneWithName(zoneName)
        
    
    def perform(self, char: Character, state: State):
        if self.zone:
            char.move(self.zone)
        else:
            char.moveRandom()
        return f"moved to zone: {char.getLocation().name}"

class KillEffect(Effect):
    args = []
    matches = ["kill"]
    
    def perform(self, char: Character, state: State):
        char.kill()
        return f"killed: {char.string()}"

class ReviveEffect(Effect):
    args = []
    matches = ["revive"]
    
    def perform(self, char: Character, state: State):
        char.revive()
        return f"revived: {char.string()}"

ALLEFFECTCLASSES: list[Type[EventPart]] = [
    AllyEffect,
    ConsumeEffect,
    ClearEffect,
    ItemEffect,
    KillEffect,
    LeaveEffect,
    MoveEffect,
    ReviveEffect,
    StatusEffect,
    TagEffect,
    UntagEffect
]

class EffectSuite(Suite):
    def __init__(self, charShort: str, argsLists: list[list[str]]):
        super().__init__(charShort, argsLists)
        self.effects: list[Effect] = []
    
    def load(self, valids: Valids):
        self.effects = []
        super().load(valids, ALLEFFECTCLASSES, self.effects)
    
    def performAll(self, char: Character, state: State):
        allEffectTexts: list[str] = []
        for effect in self.effects:
            res = effect.perform(char, state)
            allEffectTexts.append(res)
        return allEffectTexts
