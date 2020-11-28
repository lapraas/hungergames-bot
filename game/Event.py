
from __future__ import annotations
from collections import OrderedDict, defaultdict
from random import choice
import re
from typing import Union

from discord.ext.commands.core import check

from .Character import Character
from .Item import Item, Item
from .Map import Map
from .Check import CheckSuite, AliveCheck, NearbyCheck
from .Effect import EffectSuite
from .State import Result, State
from .Valids import Suite, Valids, validateText

RARITIES = {
    "common": 30,
    "uncommon": 20,
    "rare": 14,
    "rarer": 10,
    "mythic": 5,
    "secret": 3,
    "shiny": 1,
    "DEFAULT": 0
}

class Event:
    def __init__(self, name: str, chance: int, text: str, checkNamesToArgLists: dict[str, list[list[str]]], effectNamesToArgLists: dict[str, list[list[str]]], sub: list[Event]):
        self.name = name
        self.chance = chance
        self.text = text
        self.checkSuites = [CheckSuite(checkName, checkNamesToArgLists[checkName]) for checkName in checkNamesToArgLists]
        self.effectSuites = [EffectSuite(effectName, effectNamesToArgLists[effectName]) for effectName in effectNamesToArgLists]
        self.sub = sub
        self.triggerCts: dict[Character, int] = {}
    
    def __repr__(self):
        return f"Event {self.name}"
    
    def exception(self, text):
        return Exception(f"In event {self.name}: ", text)
    
    def getName(self):
        return self.name
    
    def getChance(self):
        return RARITIES[self.chance]
        
    def load(self, valids: Valids):
        try:
            for i, checkSuite in enumerate(self.checkSuites):
                checkSuite.load(valids)
                if i > 1:
                    checkSuite.addNearbyCheckIfNeeded(valids)
            for effectSuite in self.effectSuites:
                effectSuite.load(valids)
            for subEvent in self.sub:
                subEvent.load(valids)
        except Exception as e:
            raise Exception(f"Encountered an exception when loading Event \"{self.name}\": {e}")
    
    def prepare(self, mainChar: Character, otherChars: list[Character], state: State=None) -> bool:
        """
            Prepares this Event to be triggered, assigning Characters to the Event State if they match.
            If any of the requirements aren't met, returns False, otherwise returns True.
            """
        self.state = State(self.triggerCts) if not state else state
        
        if not self.state.doesCharExist(mainChar):
            return self.prepareBase(mainChar, otherChars)
        else:
            return self.prepareSub(otherChars)
    
    def prepareBase(self, mainChar: Character, otherChars: list[Character]):
        """ Prepares a base-level event. """
        # Main Character's requirements are always the first in the list of Suites
        mainCheckSuite = self.checkSuites[0]
        
        # Check the rest of the main's requirements
        if not mainCheckSuite.checkAll(mainChar, self.state): return False
        
        # If the main character matches, we put them into the State
        self.state.setChar(mainCheckSuite.getCharShort(), mainChar)
        
        # All other requirement suites match other characters from the given list of all other Characters
        for reqSuite in self.checkSuites[1:]:
            matchedChar = self.matchCharacter(reqSuite, otherChars)
            if not matchedChar: return False
            self.state.setChar(reqSuite.getCharShort(), matchedChar)
        return True
    
    def prepareSub(self, otherChars: list[Character]):
        """ Prepares a sub-event. """
        # Sub-events can have empty requirements
        if not self.checkSuites: return True
        
        for checkSuite in self.checkSuites:
            # There might already be a character in the Event State
            short = checkSuite.getCharShort()
            matchedChar = self.state.getChar(short)
            
            # If that's not the case, we want to match a new Character like normal
            if not matchedChar:
                matchedChar = self.matchCharacter(checkSuite, otherChars)
                if not matchedChar: return False
                self.state.setChar(checkSuite.getCharShort(), matchedChar)
                continue
            # If that is the case, we want to check the preexisting Character against the new requirements
            if not checkSuite.checkAll(matchedChar, self.state):
                return False
        
        return True
    
    def matchCharacter(self, checkSuite: CheckSuite, otherChars: list[Character]):
        # Collect a list of all matched Characters
        matchedChars: list[Character] = []
        
        for char in otherChars:
            # Can't match the same Character twice
            if self.state.doesCharExist(char): continue
            # Full Suite check, adding Character if it matches
            if checkSuite.checkAll(char, self.state):
                matchedChars.append(char)
        if not matchedChars:
            return False
        
        # Assign a random Character from the matcheed Characters to the State
        return choice(matchedChars)
    
    def incrementTriggers(self, char: Character):
        """ Increments the number of times this Event has been triggered by a certain Character. """
        # Count the number of triggers that have happened to the main Character
        if not char in self.triggerCts:
            self.triggerCts[char] = 0
        self.triggerCts[char] += 1
    
    def trigger(self, result: Result):
        """ Performs the Event's effects on the Characters given to the State. """
        mc = self.state.getChar()
        self.incrementTriggers(mc)
        
        result.addText(self.text, self.state)
        # Do each Suite's actions to the State's Characters
        for effectSuite in self.effectSuites:
            char = self.state.getChar(effectSuite.getCharShort())
            for effectText in effectSuite.performAll(char, self.state):
                result.addEffect(char, effectText)
        return self.state, self.sub
