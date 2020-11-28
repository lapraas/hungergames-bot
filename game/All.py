
from game.Game import Game
from game.Valids import Valids
import os
import re
from typing import Callable, Optional

from ruamel.yaml import YAML
from ruamel.yaml import events
yaml = YAML()

from .Character import Character
from .Event import Event
from .Item import Item
from .Map import Map

class LoadException(Exception):
    """ Simple class differentiating errors that happen during loading. """


commaPat = re.compile(r"\s*,\s*")
spacePat = re.compile(r"\s+")

class All:
    def __init__(self, rootPath: str, charsDirName: str="characters", itemsDirName: str="items", mapsDirName: str="maps", eventsDirName: str="events"):
        self.rootPath = rootPath
        
        self.characters: dict[str, list[Character]] = {}
        self.allCharacters: list[Character] = []
        self.build(self.charactersFromYaml, charsDirName)
        
        self.items: dict[str, list[Item]] = {}
        self.allItems: list[Item] = []
        self.build(self.itemsFromYaml, itemsDirName)
        
        self.maps: dict[str, Map] = {}
        self.allMaps: list[Map] = []
        self.build(self.mapFromYaml, mapsDirName)
        
        self.events: dict[str, list[Event]] = {}
        self.allEvents: list[Event] = []
        self.build(self.eventsFromYaml, eventsDirName)
    
    def loadGameWithSettings(self, characterFiles: list[str], itemFiles: list[str], mapFile: str, eventFiles: list[str]):
        loadedCharacters: list[Character] = self.load(characterFiles, self.characters, self.allCharacters)
        loadedItems: list[Item] = self.load(itemFiles, self.items, self.allItems)
        loadedMap: Map = self.loadOne(mapFile, self.maps)
        loadedEvents: list[Event] = self.load(eventFiles, self.events, self.allEvents)
        
        for event in loadedEvents:
            valids = Valids(loadedMap, loadedItems)
            event.load(valids)
        
        return Game(loadedItems, loadedEvents, loadedCharacters, loadedMap)
    
    def load(self, files: str, objDict: dict[str, list[object]], objList: list[object]):
        loaded = []
        for file in files:
            if file == "ALL":
                loaded = objList
                break
            toLoad = objDict.get(file)
            loaded += toLoad
        return loaded
    
    def loadOne(self, file, objDict: dict[str, object]):
        toLoad = objDict.get(file)
        return toLoad
        
    def charactersFromYaml(self, dotsName: str, yaml: dict[str, list[str]]):
        chars = []
        for name in yaml:
            data = yaml[name]
            if not len(data) >= 2:
                raise LoadException(f"Couldn't load character {name}, too few elements in list ({data})")
            
            gender = data[0]
            if gender == "male":
                pronouns = ["he", "him", "his", "his", "himself", False]
            elif gender == "female":
                pronouns = ["she", "her", "her", "hers", "herself", False]
            elif gender == "nonbinary":
                pronouns = ["they", "them", "their", "theirs", "themself", True]
            else:
                pronouns = data[0].split(" ")
                pronouns[5] = True if not pronouns[5] in ["False", "0"] else False
            
            imgSrc = data[1]
            chars.append(Character(name, imgSrc, pronouns))
        
        self.characters[dotsName] = chars
        self.allCharacters += chars
    
    def itemsFromYaml(self, dotsName: str, yaml: dict[str, str]):
        items = []
        for name in yaml:
            data = yaml[name]
            items.append(Item(name, data.split(" ")))
        
        self.items[dotsName] = items
        self.allItems += items
    
    def mapFromYaml(self, dotsName: str, yaml: dict[str, list[dict[str, str]]]):
        map = Map()
        for loc in yaml["locations"]:
            name = loc["name"]
            map.addZone(name)
        for loc in yaml["locations"]:
            name = loc["name"]
            connx = loc["connx"].split(" ")
            map.connectZone(name, connx)
        
        self.maps[dotsName] = map
        self.allMaps.append(map)
    
    def eventFromYaml(self, name: str, data: dict[str, dict[str, str]]):
        chance = data.get("chance")
        if not chance: raise LoadException(f"\"chance\" value in event {name} not found")
        
        text = data.get("text")
        if not text: raise LoadException(f"\"text\" value in event {name} not found")
        
        checks = data.get("checks")
        if not checks: checks = {}
        if type(checks) == str: raise LoadException(f"\"checks\" value in event {name} was a string (\"{checks}\"), needs to be a dict")
        
        for charShort in checks:
            argsStr = checks[charShort]
            if argsStr:
                if not type(argsStr) == str: raise LoadException(f"\"checks\" value in event {name} has an argument string ({argsStr}) of the incorrect type")
                checks[charShort] = [spacePat.split(allArgs) for allArgs in commaPat.split(argsStr)]
            else:
                checks[charShort] = []
        
        effects = data.get("effects")
        if not effects: effects = {}
        if type(effects) == str: raise LoadException(f"\"effects\" value in event {name} was a string (\"{effects}\"), needs to be a dict")
        
        for charShort in effects:
            argsStr = effects[charShort]
            if argsStr:
                if not type(argsStr) == str: raise LoadException(f"\"effects\" value in event {name} has an argument string ({argsStr}) of the incorrect type")
                effects[charShort] = [spacePat.split(allArgs) for allArgs in commaPat.split(argsStr)]
            else:
                effects[charShort] = []
        
        sub = data.get("sub")
        if not sub: sub = {}
        subEvents = []
        for subName in sub:
            subData = sub[subName]
            subEvents.append(self.eventFromYaml(subName, subData))
        
        return Event(name, chance, text, checks, effects, subEvents)
    
    def eventsFromYaml(self, dotsName: str, yaml: dict[str, dict[str, dict[str, str]]]):
        events: list[Event] = []
        for name in yaml:
            data = yaml[name]
            events.append(self.eventFromYaml(name, data))
            
        self.events[dotsName] = events
        self.allEvents += events
            
        
    def build(self, buildFun: Callable, dirName: str, baseDotsName: str=""):
        path = os.path.join(self.rootPath, dirName)
        subdirs: list[str] = []
        files: list[str] = []
        for fName in os.listdir(path):
            if os.path.isdir(os.path.join(path, fName)):
                subdirs.append(fName)
            else:
                files.append(fName)
                
        for file in files:
            if not file.endswith(".yaml"): continue
            dotsName = file.replace(".yaml", "")
            if baseDotsName:
                dotsName = baseDotsName + "." + dotsName
            with open(os.path.join(path, file), "r") as f:
                allYaml = yaml.load(f)
                if not allYaml: continue
                buildFun(dotsName, allYaml)
        
        for subdir in subdirs:
            fullPath = os.path.join(dirName, subdir)
            self.build(buildFun, fullPath, subdir)

if __name__ == "__main__":
    all = All("./yamlsources")
    print(all.characters)
    print(all.items)
    print(all.maps)
    print(all.events)
    game = all.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])
    print(game.events)
