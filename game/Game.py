
from random import choice, randint
from typing import Optional, Union

from game.Character import Character
from game.Event import Event
from game.Item import Item, Item
from game.Map import Map
from game.State import Result, State


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
        
        self.inProgress = False
        self.rounds = 0
        
        self.acted: list[Character] = []
        self.toAct: list[Character] = []
    
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
    
    def getRoundFlavor(self):
        if self.rounds == 0:
            return self.map.flavor["start"]
        else:
            return self.map.flavor.get(self.rounds)
    
    def triggerByName(self, charName, eventName) -> Union[str, Result]:
        char = self.getTributeByName(charName)
        if not char: return f"unable to find character named {charName}"
        
        event = self.getEventByName(eventName)
        if not event: return f"unable to find event named {eventName}"
        
        if event.prepare(char, self.tributes):
            return self.trigger(char, event)
        
        return "Trigger failed"
    
    def trigger(self, char: Character, event: Event, results: Optional[Result]=None) -> Optional[Result]:
        if not results:
            results = Result(char)
        state, subEvents = event.trigger(results)
        if subEvents:
            sub = self.chooseFromEvents(char, subEvents, state)
            if not sub: return results
            self.trigger(char, sub, results)
        return results
        
    def chooseFromEvents(self, char: Character, events: list[Event]=None, state: State=None) -> Optional[Event]:
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
        
        print(f"Character: {char}")
        print(f"  alive:\t{char.alive}")
        print(f"  age:\t{char.age}")
        print(f"  location:\t{char.location}")
        print(f"  status:\t{char.status}")
        print(f"  tags:")
        [print(f"    {tag}") for tag in char.tags]
        print(f"  inventory:\t{char.items}")
        print(f"  alliance:\t{char.alliance}")
        print(f"Possible events: {possibleEvents}")
        print(f"Default event: {defaultEvent}\n")
        
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
        if not char.isAlive():
            return None
        raise Exception(f"Invalid choice when choosing from events ({choice} out of {totalChance})")
    
    def start(self):
        """ Starts the game, resetting all tributes and troves. """
        
        if self.inProgress: return False
        self.inProgress = True
        for tribute in self.tributes.values():
            tribute.reset()
            tribute.move(self.map.getStartingZone())
        for trove in self.map.troves.values():
            trove.reset()
            trove.load(self.items)
        return True
    
    def round(self) -> Optional[bool]:
        """ Starts a game round. Increments the age of all tributes. """
        if self.toAct: return True
        if not self.inProgress: return False
        self.rounds += 1
        
        self.acted = []
        self.toAct = []
        for tribute in self.tributes.values():
            tribute.incAge()
            self.toAct.append(tribute)
    
    def next(self) -> Union[Result, bool, None]:
        """ Progresses a game round.
            Chooses a random tribute that hasn't acted and triggers an Event for them. """
        
        if not self.inProgress: return False
        
        if not self.toAct: self.round()
        
        acting = choice(self.toAct)
        self.toAct.remove(acting)
        event = self.chooseFromEvents(acting)
        if not event: return None
        result = self.trigger(acting, event)
        return result
    
    def isRoundGoing(self) -> bool:
        return len(self.toAct) > 0
        
