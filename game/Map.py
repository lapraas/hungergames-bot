
from __future__ import annotations
from game.Item import Item
from random import choice
from typing import Union

class Zone:
    def __init__(self, name: str):
        self.name = name
        self.connections: list[Zone] = []
    
    def connect(self, zone: Zone):
        if zone in self.connections: return
        self.connections.append(zone)
    
    def getRandomConnection(self):
        return choice(self.connections)
    
    def getConnectionStr(self):
        if not self.connections: return "No connections"
        return "Connects to " + ", ".join([con.name for con in self.connections])
                

class Map:
    def __init__(self):
        self.zones: dict[str, Zone] = {}
        self.startingZone: Zone = None
    
    def addZone(self, name: str):
        if not self.startingZone: self.startingZone = Zone(name)
        self.zones[name] = self.startingZone
    
    def getZoneWithName(self, name: str):
        for zoneName in self.zones:
            if zoneName == name:
                return self.zones[zoneName]
        return None
    
    def connectZone(self, name: str, connx: str):
        zone = self.getZoneWithName(name)
        for conn in connx:
            otherZone = self.getZoneWithName(conn)
            zone.connect(otherZone)
            otherZone.connect(zone)
    
    def getStartingZone(self):
        return self.startingZone
    
    def getSortedZones(self):
        return [(name, self.zones[name]) for name in sorted(self.zones.keys())]
