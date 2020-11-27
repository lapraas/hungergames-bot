
from __future__ import annotations
from random import choice
import re
from typing import Union

from game.Character import Character
from game.Item import Item, Item
from game.Map import Map
from game.Requirement import ALLREQCLASSES
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
    "shiny": 1
}

class Event:
    def __init__(self, name: str, chance: int, text: str, req: list[Suite], res: list[Suite], sub: list[Event]):
        self.name = name
        self.chance = chance
        self.text = text
        self.req = req
        self.res = res
        self.sub = sub
    
    def __repr__(self):
        return f"Event {self.name}"
    
    def exception(self, text):
        return Exception(f"In event {self.name}: ", text)
    
    def getName(self):
        return self.name
    
    def getChance(self):
        return RARITIES[self.chance]
    
    def prepare(self, mainChar: Character, otherChars: list[Character], state: State=None):
        self.state = State()
        if state:
            self.state = state
        
        if not self.req:
            if not state.hasMainCharacter():
                raise Exception("There were no requirements for this non-sub-event")
            else:
                return True
        mainReq = self.req[0]
        if not mainReq.check(mainChar, self.state):
            return False
            
        self.state.setChar(mainReq.getCharShort(), mainChar)
        
        for req in self.req[1:]:
            possibleChars: list[Character] = []
            for char in otherChars:
                if self.state.doesCharExist(char): continue
                if req.check(char, self.state):
                    possibleChars.append(char)
            if not possibleChars:
                return False
                
            self.state.setChar(req.getCharShort(),  choice(possibleChars))
            
        return True
    
    def trigger(self):
        for resSuite in self.res:
            char = self.state.getChar(resSuite.getCharShort())
            for resText in resSuite.perform(char, self.state):
                self.state.addResText(char, resText)
        return self.state, self.sub

class EventLoadException(Exception):
    def __init__(self, eventName, message):
        super().__init__(f"in event \"{eventName}\", {message}")

def _loadEvent(name: str, data: dict[str, Union[int, str, dict[str, str]]], valids: Valids):
    chance = data.get("chance")
    if not chance:
        raise EventLoadException(name, "chance parameter not found")
    
    text = data.get("text")
    if not text:
        raise EventLoadException(name, "text parameter not found")
    if text[-1] == "\n":
        text = text[:-1]
    
    commaPat = re.compile(r"\s*,\s*")
    spacePat = re.compile(r"\s+")
    req = data.get("req")
    if not req: req = []
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
    events: list[Event] = []
    for name in yaml:
        data = yaml[name]
        valids = Valids(allItems, map)
        events.append(_loadEvent(name, data, valids))
    return events
