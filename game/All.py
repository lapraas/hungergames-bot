
from collections import OrderedDict
import os
from os import stat
import re
from typing import Any, Callable, Union

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString as YAMLString
yaml = YAML()

from game.Character import Character
from game.Event import Event
from game.Item import Item
from game.Map import Map
from game.Trove import Trove
from game.Game import Game
from game.Valids import Valids

class LoadException(Exception):
    """ Simple class differentiating errors that happen during loading. """

commas = re.compile(r"\s*,\s*")
spaces = re.compile(r"\s+")
semicolons = re.compile(r"\s*;\s*")
newlines = re.compile(r"\n+")

class All:
    def __init__(self, rootPath: str, charsDirName: str="characters", itemsDirName: str="items", mapsDirName: str="maps", eventsDirName: str="events"):
        self.rootPath = rootPath
        
        self.charsDirName = charsDirName
        self.characters: dict[str, dict[str, Character]] = {}
        self.allCharacters: dict[str, Character] = {}
        res = self.build(self.charactersFromYaml, self.charsDirName)
        if res: raise LoadException(res)
        
        self.itemsDirName = itemsDirName
        self.items: dict[str, dict[str, Item]] = {}
        self.allItems: dict[str, Item] = {}
        res = self.build(self.itemsFromYaml, self.itemsDirName)
        if res: raise LoadException(res)
        
        self.mapsDirName = mapsDirName
        self.maps: dict[str, Map] = {}
        res = self.build(self.mapFromYaml, self.mapsDirName)
        if res: raise LoadException(res)
        
        self.eventsDirName = eventsDirName
        self.events: dict[str, dict[str, Event]] = {}
        self.allEvents: list[Event] = {}
        res = self.build(self.eventsFromYaml, self.eventsDirName)
        if res: raise LoadException(res)
    
    def loadGameWithSettings(self, characters: list[str], items: list[str], map: str, events: list[str]) -> Game:
        loadedCharacters: dict[str, Character] = All.load(characters, self.characters)
        loadedItems: dict[str, Item] = All.load(items, self.items)
        loadedMap: Map = All.loadOne(map, self.maps)
        loadedEvents: dict[str, Event] = All.load(events, self.events)
        
        for event in loadedEvents.values():
            valids = Valids(loadedMap, loadedItems)
            event.load(valids)
        
        return Game(loadedItems, loadedEvents, loadedCharacters, loadedMap)
    
    @staticmethod
    def load(files: str, objsPerFile: dict[str, dict[str, Any]]) -> dict[str, Any]:
        loaded = {}
        for file in files:
            found = False
            for dotsName in objsPerFile:
                if dotsName.startswith(file):
                    found = True
                    toLoad = objsPerFile.get(dotsName)
                    loaded = {**loaded, **toLoad}
            if not found:
                raise LoadException(f"Couldn't find any game object files with the name {file}")
        return loaded
    
    @staticmethod
    def loadOne(file, objDict: dict[str, object]) -> Any:
        toLoad = objDict.get(file)
        if not toLoad:
            raise LoadException(f"Couldn't find any game object files with the name {file}")
        return toLoad
    
    def dotPathToReal(self, dirName: str, dotPath: str) -> str:
        path = os.path.join(self.rootPath, dirName, *dotPath.split("."))
        return path + ".yaml"
    
    @staticmethod
    def getYamlFromFile(filename: str) -> dict:
        with open(filename, "r") as f:
            allYaml = yaml.load(f)
            if not allYaml: allYaml = {}
            return allYaml
    
    @staticmethod
    def replaceYamlInFile(filename: str, allYaml: str) -> None:
        with open(filename, "w") as f:
            yaml.dump(allYaml, f)
            
    def build(self, buildFun: Callable, dirName: str, baseDotsName: str="") -> None:
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
            allYaml = All.getYamlFromFile(os.path.join(path, file))
            try:
                buildFun(dotsName, allYaml)
            except LoadException as e:
                raise LoadException(f"In file {dotsName}: {e}")
        
        for subdir in subdirs:
            fullPath = os.path.join(dirName, subdir)
            self.build(buildFun, fullPath, subdir)
        
    def create(self, name: str, data: Any, buildFun: Callable[[str, Any], Any], objsPerFile: dict[str, dict[str, Any]], allObjs: dict[str, Any], dotFileName) -> None:
        if not dotFileName in objsPerFile: raise LoadException(f"Couldn't find a file at {dotFileName}")
        if name in allObjs: raise LoadException(f"Tried to create duplicate `{name}`")
        
        targetFilePath = self.dotPathToReal(self.charsDirName, dotFileName)
        allYaml = All.getYamlFromFile(targetFilePath)
        
        new = buildFun(name, data)
        allYaml[name] = data
        All.replaceYamlInFile(targetFilePath, allYaml)
        
        objsPerFile[dotFileName][name] = new
        allObjs[name] = new
    
    ###
    # Character
    ###
    
    @staticmethod
    def characterFromYaml(name: str, data: tuple[str, str]) -> Character:
        if not len(data) >= 2: raise LoadException(f"Couldn't load character {name}, too few elements in list ({data})")
        
        gender = data[0]
        if gender == "male":
            pronouns = ["he", "him", "his", "his", "himself"]
        elif gender == "female":
            pronouns = ["she", "her", "her", "hers", "herself"]
        elif gender == "nonbinary":
            pronouns = ["they", "them", "their", "theirs", "themself"]
        else:
            pronouns = data[0].split(" ")
            if len(pronouns) != 5:
                raise LoadException(f"Couldn't load Character {name}, there were not 5 values for the Character's pronouns ({pronouns})")
        
        imgSrc = data[1]
        return Character(name, imgSrc, pronouns)
    
    def charactersFromYaml(self, dotsName: str, yaml: dict[str, list[str]]) -> None:
        chars: dict[str, Character] = {}
        
        for name in yaml:
            if name in self.allCharacters: raise LoadException(f"Encountered duplicate Character {name} in file {dotsName}")
            data = yaml[name]
            char = All.characterFromYaml(name, data)
            chars[name] = char
            self.allCharacters[name] = char
        
        self.characters[dotsName] = chars
    
    def addCharacter(self, name: str, data: tuple[str, str], dotFileName="adds"):
        self.create(name, data, All.characterFromYaml, self.characters, self.allCharacters, dotFileName)
    
    ###
    # Item
    ###
    
    @staticmethod
    def itemFromYaml(name: str, data: str) -> Item:
        if not data: raise LoadException(f"There was no tag list for item {name}")
        return Item(name, data.split(" "))
    
    def itemsFromYaml(self, dotsName: str, yaml: dict[str, str]) -> None:
        items: dict[str, Item] = {}
        
        for name in yaml:
            if name in self.allItems: raise LoadException(f"Encountered duplicate Item {name} in file {dotsName}")
            
            data = yaml[name]
            item = All.itemFromYaml(name, data)
            items[name] = item
            self.allItems[name] = item
        
        self.items[dotsName] = items
    
    def addItem(self, name: str, data: str, dotFileName="adds"):
        self.create(name, data, All.itemFromYaml, self.items, self.allItems, dotFileName)
    
    ###
    # Map
    ###
    
    def mapFromYaml(self, dotsName: str, yaml: dict[str, dict[str, Union[str, dict[str, Union[str, int]]]]]) -> None:
        map = Map()
        zones = yaml.get("zones")
        if not isinstance(zones, dict): raise LoadException(f"`zones` value in Map was not a dict (got: {zones})")
        
        for locName in zones:
            map.addZone(locName)
        for locName in zones:
            data = zones[locName]
            if not data: continue
            if data and not isinstance(data, str): raise LoadException(f"`{locName}` value in map was not a str (got: {data})")
            connections = data.split(", ")
            for connection in connections:
                if not map.getZone(connection): LoadException(f"Found invalid connection `{connection}` in `{locName}` in Map")
            map.connectZone(locName, connections)
        
        troves = yaml.get("troves", {})
        if not isinstance(troves, dict): raise LoadException(f"`troves` value in Map was not a dict (got: {troves})")
        
        for troveName in troves:
            data = troves[troveName]
            pool = data.get("pool", [])
            count = data.get("count", 0)
            if pool and not count: raise LoadException(f"Trove had `pool` value but no `count` value, `count` must be at least 1")
            if (not pool) and count: raise LoadException(f"Trove had `count` value but no `pool` value, `pool` must exist to randomly choose Items")
            has = data.get("has", [])
            if not (pool or has): raise LoadException(f"Trove requires either `pool` or `has` values, neither were found in Trove `{troveName}`")
            if pool:
                pool = commas.split(pool)
                pool = [spaces.split(tags) for tags in pool]
                for tags in pool:
                    if tags[0] == "": raise LoadException(f"Got an empty `pool` tag list entry")
            if has:
                has = commas.split(has)
            trove = Trove(troveName, count, pool, has)
            map.addTrove(trove)
        
        self.maps[dotsName] = map
    
    ###
    # Event
    ###
    @staticmethod
    def eventFromYamlNew(name: str, data: OrderedDict[str, Union[str, int, OrderedDict]], defaultReq: str=""):
        text: str = None
        checks: dict[str, list[list[str]]] = {}
        effects: dict[str, list[list[str]]] = {}
        
        if not isinstance(data, dict): raise LoadException(f"Data for event {name} was not a dict (got: {data})")
        
        print(f"Beginning load for event {name}")
        
        subEvents = []
        
        for key in data:
            val = data[key]
            if key == "text":
                if not isinstance(val, str): raise LoadException(f"`text` value in event {name} was not a string (got: {val})")
                text = [t.strip() for t in newlines.split(val.strip())]
            elif key.startswith("->"):
                if not isinstance(val, dict): raise LoadException(f"`->` (sub) value in event {name} was not a dict (got: {val})")
                subEvents.append(All.eventFromYamlNew(name + key, val, defaultReq))
            else:
                if not val: val = ""
                if not any([isinstance(val, str), isinstance(val, int)]): raise LoadException(f"`{key}` value in event {name} was not a string or int (got: {val})")
                charShort = str(key)
                parts = semicolons.split(val)
                if len(parts) > 2: raise LoadException(f"`{charShort}` value in event {name} had too many semicolons (got: {val})")
                reqStr = parts[0]
                resStr = parts[1] if len(parts) == 2 else ""
                if defaultReq: # one off - only apply default to the main char requirement
                    if reqStr:
                        reqStr = defaultReq + ", " + reqStr
                    else:
                        reqStr = defaultReq
                    defaultReq = None
                checks[charShort] = [spaces.split(allArgs) for allArgs in commas.split(reqStr)] if reqStr else []
                effects[charShort] = [spaces.split(allArgs) for allArgs in commas.split(resStr)] if resStr else []
        
        if text == None: raise LoadException(f"`text` value in event {name} not found")
        
        return Event(name, text, checks, effects, subEvents)
    
    def eventsFromYaml(self, dotsName: str, yaml: dict[str, Union[str, dict[str, Union[str, dict[str, str]]]]]) -> None:
        events: dict[str, Event] = {}
        
        defaultReq: str = ""
        for name in yaml:
            data = yaml[name]
        
            if name.startswith("USING"):
                if not data:
                    defaultReq = ""
                elif not type(data) == str:
                    raise LoadException(f"Encountered `USING` entry but the value was not a string (got: {data})")
                defaultReq = data
                continue
            
            name = dotsName + "." + name
            event = All.eventFromYamlNew(name, data, defaultReq)
            events[name] = event
            
        self.events[dotsName] = events

if __name__ == "__main__":
    all = All("./yamlsources")
    print(all.characters)
    print(all.items)
    print(all.maps)
    print(all.events)
    game = all.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])
    print(game.events)
