
from __future__ import annotations
from typing import Union
from game.Item import Item
from game.Trove import Trove
from random import choice

class Zone:
    def __init__(self, name: str):
        self.name = name
        self.connections: list[Zone] = []
    
    def __str__(self):
        return f"Zone \"{self.name}\""
    
    def connect(self, zone: Zone):
        if zone in self.connections: return
        self.connections.append(zone)
    
    def getRandomConnection(self):
        if not self.connections: return self
        return choice(self.connections)
    
    def getConnectionStr(self):
        if not self.connections: return "No connections"
        return "Connects to " + ", ".join([con.name for con in self.connections])
                

class Map:
    def __init__(self, flavor: dict[Union[str, int], str]):
        self.flavor = flavor
        
        self.zones: dict[str, Zone] = {}
        self.troves: dict[str, Trove] = {}
        self.startingZone: Zone = None
    
    def addZone(self, name: str):
        zone = Zone(name)
        if not self.startingZone:
            self.startingZone = zone
        self.zones[name] = zone
    
    def addTrove(self, trove: Trove):
        self.troves[trove.getName()] = trove
    
    def getZone(self, name: str):
        return self.zones.get(name)
    
    def getTrove(self, name: str):
        return self.troves.get(name)
    
    def loadTroves(self, loadedItems: dict[str, Item]):
        for trove in self.troves.values():
            res = trove.load(loadedItems)
            if res: return res
    
    def connectZone(self, name: str, connx: str):
        zone = self.getZone(name)
        for conn in connx:
            otherZone = self.getZone(conn)
            zone.connect(otherZone)
            otherZone.connect(zone)
    
    def getStartingZone(self):
        return self.startingZone
    
    def getSortedZones(self):
        return [(name, self.zones[name]) for name in sorted(self.zones.keys())]
