
from __future__ import annotations
from collections import OrderedDict, defaultdict
from random import choice
import re
from typing import Union

from discord.ext.commands.core import check

from game.Character import Character
from game.Item import Item, Item
from game.Map import Map
from game.Requirement import ALLREQCLASSES, AliveReq, NearbyReq
from game.Result import ALLRESCLASSES
from game.State import State
from game.Valids import Suite, Valids, validateText

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

defaultAlive = AliveReq(None, "alive")
defualtNearby = NearbyReq(None, "nearby")

class Event:
    def __init__(self, name: str, chance: int, text: str, req: list[Suite], res: list[Suite], sub: list[Event]):
        self.name = name
        self.chance = chance
        self.text = text
        self.reqSuites = req
        self.resSuites = res
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
    
    def prepareSub(self, otherChars: list[Character]):
        """ Prepares a sub-event. """
        # Sub-events can have empty requirements
        if not self.reqSuites: return True
        
        for reqSuite in self.reqSuites:
            # There might already be a character in the Event State
            short = reqSuite.getCharShort()
            matchedChar = self.state.getChar(short)
            
            # If that's not the case, we want to match a new Character like normal
            if not matchedChar:
                matchedChar = self.matchCharacter(reqSuite, otherChars)
                if not matchedChar: return False
                self.state.setChar(reqSuite.getCharShort(), matchedChar)
                continue
            # If that is the case, we want to check the preexisting Character against the new requirements
            if not reqSuite.check(matchedChar, self.state):
                return False
        
        return True
    
    def prepareBase(self, mainChar: Character, otherChars: list[Character]):
        """ Prepares a base-level event. """
        # Main Character's requirements are always the first in the list of Suites
        mainReqSuite = self.reqSuites[0]
        # Check to see if the mainChar is alive, but only if there are no AliveReqs in the Suite
        if (not any([type(req) == AliveReq for req in mainReqSuite.eventParts])):
            if not defaultAlive.do(mainChar, self.state): return False
        
        # Check the rest of the main's requirements
        if not mainReqSuite.check(mainChar, self.state): return False
        
        # If the main character matches, we put them into the State
        self.state.setChar(mainReqSuite.getCharShort(), mainChar)
        
        # All other requirement suites match other characters from the given list of all other Characters
        for reqSuite in self.reqSuites[1:]:
            matchedChar = self.matchCharacter(reqSuite, otherChars)
            if not matchedChar: return False
            self.state.setChar(reqSuite.getCharShort(), matchedChar)
        return True
    
    def matchCharacter(self, reqSuite: Suite, otherChars: list[Character]):
        # Collect a list of all matched Characters
        matchedChars: list[Character] = []
        
        # Boolean values that determine whether or not we're doing the default checks
        checkAlive = not any([type(req) == AliveReq for req in reqSuite.eventParts])
        checkNearby = not any([type(req) == NearbyReq for req in reqSuite.eventParts])
        
        for char in otherChars:
            # Can't match the same Character twice
            if self.state.doesCharExist(char): continue
            # Default checks if necessary
            if checkAlive and not defaultAlive.do(char, self.state): continue
            if checkNearby and not defualtNearby.do(char, self.state): continue
            # Full Suite check, adding Character if it matches
            if reqSuite.check(char, self.state):
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
    
    def trigger(self):
        """ Performs the Event's effects on the Characters given to the State. """
        mc = self.state.getChar()
        self.incrementTriggers(mc)
        
        # Do each Suite's actions to the State's Characters
        for resSuite in self.resSuites:
            char = self.state.getChar(resSuite.getCharShort())
            for resText in resSuite.perform(char, self.state):
                self.state.addResText(char, resText)
        return self.state, self.sub

class EventLoadException(Exception):
    def __init__(self, eventName, message):
        super().__init__(f"in event \"{eventName}\", {message}")

def _loadEvent(name: str, data: dict[str, Union[int, str, dict[str, str]]], valids: Valids):
    """ Builds an Event from a YAML object, using a unique Valids object.
        Raises any Exceptions that the Event encounters in its creation as EventLoadExceptions. """
    chance = data.get("chance")
    if not chance:
        raise EventLoadException(name, "`chance` value not found")
    
    text = data.get("text")
    if not text:
        raise EventLoadException(name, "`text` value not found")
    if text[-1] == "\n":
        text = text[:-1]
    
    commaPat = re.compile(r"\s*,\s*")
    spacePat = re.compile(r"\s+")
    req = data.get("req")
    if not req:
        req = {}
    if type(req) == str:
        raise EventLoadException(name, f"bad value for `req` was found: \"{req}\"")
    reqSuites: list[Suite] = []
    
    for charShort in req:
        allRequirementsStr = req.get(charShort)
        reqs: list[list[str]] = []
        if allRequirementsStr and type(allRequirementsStr) == str:
            reqs = commaPat.split(allRequirementsStr)
            reqs = [spacePat.split(req) for req in reqs]
        try:
            reqSuite = Suite(charShort, ALLREQCLASSES, reqs, valids)
        except Exception as e:
            raise EventLoadException(name, str(e))
        reqSuites.append(reqSuite)
        
    res = data.get("res")
    if not res: res = []
    resSuites: list[Suite] = []
    for charShort in res:
        allResultsStr = res.get(charShort)
        ress: list[list[str]] = []
        if allResultsStr and type(allResultsStr) == str:
            ress = commaPat.split(allResultsStr)
            ress = [spacePat.split(res) for res in ress]
        try:
            resSuite = Suite(charShort, ALLRESCLASSES, ress, valids)
        except Exception as e:
            raise EventLoadException(name, str(e))
        resSuites.append(resSuite)
    
    try:
        validateText(text, valids)
    except Exception as e:
        raise EventLoadException(name, str(e))
    
    sub = []
    allSubEvents = data.get("sub")
    if allSubEvents:
        for subName in allSubEvents:
            subData = allSubEvents[subName]
            sub.append(_loadEvent(subName, subData, valids))
            
    return Event(name, chance, text, reqSuites, resSuites, sub)

def buildEventsFromYaml(yaml: dict[str, dict[str, dict[str, str]]], allItems: list[Item], map: Map):
    """ Builds a list of events from a YAML object. """
    events: list[Event] = []
    for name in yaml:
        data = yaml[name]
        valids = Valids(allItems, map)
        events.append(_loadEvent(name, data, valids))
    return events
