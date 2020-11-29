
from __future__ import annotations
import re
from typing import Optional, Union

from .Character import Character
from .Item import Item

class State:
    """ This is a more temporary counterpart to Valids.
        It stores the Event's matched game objects, such as Characters and Items, and is given to each EventPart to check against / add to.
        It also compiles each of the Results' strings with the Character the Result was performed on.
        """
    
    def __init__(self, eventTriggers: dict[Character, int]):
        self.eventTriggers = eventTriggers
        
        self.charsPool = {}
        self.itemsPool = {}
        self.mainCharShort: str = None
        
        self.resultStrs: dict[Character, list[str]] = {}
    
    def getTriggersFor(self, char: Character):
        """ Gets the number of times the State's Event has triggered for a certain Character. """
        return self.eventTriggers.get(char, 0)
    
    def getTotalTriggers(self):
        """ Gets the total number of times the State's Event has triggered. """
        return sum(self.eventTriggers.values())
    
    def setChar(self, charShort: str, char: Character):
        """ Adds a Character to the State, matched to a shorthand. """
        self.charsPool[charShort] = char
        if not self.mainCharShort:
            self.mainCharShort = charShort
    
    def setItem(self, itemShort: str, item: Item):
        """ Adds an Item to the State, matched to a shorthand. """
        self.itemsPool[itemShort] = item
    
    def getChar(self, charShort: str=None) -> Optional[Character]:
        """ Gets a Character matched to a shorthand. If no shorthand is given, the main Character is gotten and returned. """
        if not charShort:
            if not self.mainCharShort: return None
            return self.getChar(self.mainCharShort)
        return self.charsPool.get(charShort)
    
    def doesCharExist(self, char: Character) -> bool:
        """ Gets whether or not a Character object exists in the State. """
        return char in self.charsPool.values()
    
    def getShortForChar(self, char: Character) -> Optional[str]:
        """ Gets the shorthand for a Character object. Used in the Event's re-requirements. """
        for short in self.charsPool:
            if char == self.getChar(short):
                return short
        return None
    
    def getItem(self, itemShort: str) -> Optional[Item]:
        """ Gets an Item matched to a shorthand. """
        return self.itemsPool.get(itemShort)

class Result:
    def __init__(self, mainChar: Character):
        self.mainChar = mainChar
        self.effects: dict[Character, list[str]] = {}
        self.texts: list[str] = []
    
    def addEffect(self, affected: Character, text: str):
        if not affected in self.effects:
            self.effects[affected] = []
        self.effects[affected].append(text)
    
    def addText(self, text: str, state: State):
        """ Replaces all shorthands in an Event's text result with their respective Character or Item.
            Also handles pronouns, articles, and verb conjugation.
            Adds the replaced text. """
        textReplacePat = re.compile(r"([A-Za-z']*)(@|&)(\w+)")
        matches = textReplacePat.finditer(text)
        offset = 0
        for match in matches:
            toConj, objType, short = match.groups()
            replaceObj = None
            if objType == "@":
                replaceObj = state.getChar(short)
            elif objType == "&":
                replaceObj = state.getItem(short)
            replaceText = replaceObj.string(toConj)
            
            text = text[:match.start() - offset] + replaceText + text[match.end() - offset:]
            letterDiff = match.end() - match.start() - len(replaceText)
            offset += letterDiff
        
        self.texts.append(text)
    
    def getMainChar(self):
        return self.mainChar
    
    def getEffects(self):
        return self.effects
    
    def getTexts(self):
        return self.texts
