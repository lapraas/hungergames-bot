
from random import randint

from Character import Character
from Event import Event
from Item import Item, Item
from Map import Map
from State import State


class Game:
    def __init__(self, items: list[Item], events: list[Event], tributes: list[Character], map: Map):
        self.tributes = tributes
        self.items = items
        self.events = events
        self.map = map
        
        self.acting = [] # populated on round start
        self.acted = [] # populated as events are done with tributes
        
        self.start()
    
    def start(self):
        for tribute in self.tributes:
            tribute.move(self.map.getStartingZone())
            tribute.addTag("running")
    
    def getTributeByName(self, name: str):
        for tribute in self.tributes:
            if tribute.string() == name:
                return tribute
        return None
    
    def getItemByName(self, name: str):
        for item in self.items:
            if item.string() == name:
                return item
        return None
    
    def triggerByName(self, charName, eventName) -> list[tuple[str, list[tuple[Character, str]]]]:
        char = None
        for tribute in self.tributes:
            if tribute.string() == charName:
                char = tribute
                break
        if not char:
            return [(f"unable to find character named {charName}", [])]
        event = None
        for e in self.events:
            if e.getName() == eventName:
                event = e
                break
        if not event:
            return [(f"unable to find event named {eventName}", [])]
        if event.prepare(char, self.tributes):
            return self.trigger(char, event)
        
        return [("Trigger failed", [])]
    
    def trigger(self, char: Character, event: Event):
        state, subEvents = event.trigger()
        textResults: list[tuple[str, list[tuple[Character, str]]]] = [(state.addReplacedText(event.text), state.getResTexts())]
        #print(textResults)
        if subEvents:
            sub = self.chooseFromEvents(char, subEvents, state)
            textResults += self.trigger(char, sub)
        return textResults
        
    def chooseFromEvents(self, char: Character, events: list[Event]=None, state: State=None):
        if not events:
            events = self.events
        
        possibleEvents: list[Event] = []
        totalChance = 0
        
        for event in events:
            if event.prepare(char, self.tributes, self.items, state):
                possibleEvents.append(event)
                totalChance += event.getChance()
        
        if not possibleEvents: raise Exception("No events matched when choosing from events")
        choice = randint(0, totalChance - 1)
        
        count = 0
        for event in possibleEvents:
            if choice >= count and choice < (count + event.chance):
                return event
            count = count + event.chance
        raise Exception(f"Invalid choice when choosing from events ({choice} out of {totalChance})")

