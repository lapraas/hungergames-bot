
from random import randint
from typing import Optional, Union

from .Character import Character
from .Event import Event
from .Item import Item, Item
from .Map import Map
from .State import Result, State


class Game:
    def __init__(self, items: dict[str, Item], events: dict[str, Event], tributes: dict[str, Character], map: Map):
        self.tributes = tributes
        self.items = items
        self.events = events
        self.map = map
        
        self.sortedTributes = [(name, self.tributes[name]) for name in sorted(self.tributes.keys())]
        self.sortedItems = [(name, self.items[name]) for name in sorted(self.items.keys())]
        self.sortedEvents = [(name, self.events[name]) for name in sorted(self.events.keys())]
        self.sortedZones = self.map.getSortedZones()
        
        self.start()
    
    def start(self):
        for tribute in self.tributes.values():
            tribute.reset()
            tribute.move(self.map.getStartingZone())
            tribute.addTag("running")
    
    def getTributeByName(self, name: str):
        return self.tributes.get(name)
    
    def getItemByName(self, name: str):
        return self.items.get(name)
    
    def getEventByName(self, name: str):
        return self.events.get(name)
    
    def getZoneByName(self, name: str):
        return self.map.getZone(name)
    
    def getSortedTributes(self):
        return self.sortedTributes
    
    def getSortedItems(self):
        return self.sortedItems
    
    def getSortedEvents(self):
        return self.sortedEvents
    
    def getSortedZones(self):
        return self.sortedZones
    
    def triggerByName(self, charName, eventName) -> Union[str, Result]:
        char = self.getTributeByName(charName)
        if not char: return f"unable to find character named {charName}"
        
        event = self.getEventByName(eventName)
        if not event: return f"unable to find event named {eventName}"
        
        if event.prepare(char, self.tributes):
            return self.trigger(char, event)
        
        return "Trigger failed"
    
    def trigger(self, char: Character, event: Event, results: Optional[Result]=None) -> Result:
        if not results:
            results = Result(char)
        state, subEvents = event.trigger(results)
        if subEvents:
            sub = self.chooseFromEvents(char, subEvents, state)
            self.trigger(char, sub, results)
        return results
        
    def chooseFromEvents(self, char: Character, events: list[Event]=None, state: State=None):
        if not events:
            events = self.events.values()
        
        possibleEvents: list[Event] = []
        totalChance = 0
        defaultEvent: Optional[Event] = None
        
        for event in events:
            if event.prepare(char, self.tributes, state):
                if event.getChance() == 0:
                    defaultEvent = event
                    continue
                totalChance += event.getChance()
                possibleEvents.append(event)
        
        if not possibleEvents:
            if defaultEvent:
                return defaultEvent
            else:
                raise Exception("No events matched when choosing from events")
                
        choice = randint(0, totalChance - 1)
        
        count = 0
        for event in possibleEvents:
            if choice >= count and choice < (count + event.getChance()):
                return event
            count = count + event.getChance()
        raise Exception(f"Invalid choice when choosing from events ({choice} out of {totalChance})")
    
    def round(self) -> dict[Character, Result]:
        allresults = {}
        for tribute in self.tributes.values():
            if not tribute.isAlive():
                continue
            event = self.chooseFromEvents(tribute)
            allresults[tribute] = self.trigger(tribute, event)
        return allresults
            
        
