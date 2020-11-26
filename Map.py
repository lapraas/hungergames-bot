
from __future__ import annotations
from random import choice

class Zone:
    def __init__(self, name: str):
        self.name = name
        self.connx: list[Zone] = []
    
    def connect(self, zone: Zone):
        if zone in self.connx: return
        self.connx.append(zone)
    
    def getRandomConnx(self):
        return choice(self.connx)

class Map:
    def __init__(self):
        self.zones: list[Zone] = []
    
    def addZone(self, name):
        self.zones.append(Zone(name))
    
    def getZoneWithName(self, name: str):
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None
    
    def connectZone(self, name: str, connx: str):
        zone = self.getZoneWithName(name)
        for conn in connx:
            otherZone = self.getZoneWithName(conn)
            zone.connect(otherZone)
            otherZone.connect(zone)
    
    def getStartingZone(self):
        return self.zones[0]

def buildZoneEventPaths(yaml: dict[str, list[dict[str, str]]]):
    events: list[str] = []
    for loc in yaml["locations"]:
        new = loc["events"]
        if not new: continue
        events.append(new.split(" "))
    return events

def buildMapFromYaml(yaml: dict[str, list[dict[str, str]]]):
    map = Map()
    for loc in yaml["locations"]:
        name = loc["name"]
        map.addZone(name)
    for loc in yaml["locations"]:
        name = loc["name"]
        connx = loc["connx"].split(" ")
        map.connectZone(name, connx)
    return map
