
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
    
    def loadGameWithSettings(self, characters: list[str], items: list[str], map: str, events: list[str]):
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
    
    def dotPathToReal(self, dirName: str, dotPath: str):
        path = os.path.join(self.rootPath, dirName, *dotPath.split("."))
        return path + ".yaml"
    
    @staticmethod
    def getYamlFromFile(filename: str):
        with open(filename, "r") as f:
            allYaml = yaml.load(f)
            if not allYaml: allYaml = {}
            return allYaml
    
    @staticmethod
    def replaceYamlInFile(filename: str, allYaml: str):
        with open(filename, "w") as f:
            yaml.dump(allYaml, f)
            
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
            allYaml = All.getYamlFromFile(os.path.join(path, file))
            try:
                buildFun(dotsName, allYaml)
            except LoadException as e:
                raise LoadException(f"In file {dotsName}: {e}")
        
        for subdir in subdirs:
            fullPath = os.path.join(dirName, subdir)
            self.build(buildFun, fullPath, subdir)
        
    def create(self, name: str, data: Any, buildFun: Callable[[str, Any], Any], objsPerFile: dict[str, dict[str, Any]], allObjs: dict[str, Any], dotFileName):
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
    def characterFromYaml(name: str, data: tuple[str, str]):
        if not len(data) >= 2: raise LoadException(f"Couldn't load character {name}, too few elements in list ({data})")
        
        gender = data[0]
        if gender == "male":
            pronouns = ["he", "him", "his", "his", "himself", False]
        elif gender == "female":
            pronouns = ["she", "her", "her", "hers", "herself", False]
        elif gender == "nonbinary":
            pronouns = ["they", "them", "their", "theirs", "themself", True]
        else:
            pronouns = data[0].split(" ")
            if len(pronouns) != 6:
                raise LoadException(f"Couldn't load Character {name}, there were not 6 values for the Character's pronouns ({pronouns})")
            pronouns[5] = True if not pronouns[5] in ["False", "0"] else False
        
        imgSrc = data[1]
        return Character(name, imgSrc, pronouns)
    
    def charactersFromYaml(self, dotsName: str, yaml: dict[str, list[str]]):
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
    def itemFromYaml(name: str, data: str):
        if not data: raise LoadException(f"There was no tag list for item {name}")
        return Item(name, data.split(" "))
    
    def itemsFromYaml(self, dotsName: str, yaml: dict[str, str]):
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
    
    def mapFromYaml(self, dotsName: str, yaml: dict[str, dict[str, Union[str, dict[str, Union[str, int]]]]]):
        map = Map()
        zones = yaml.get("zones")
        if not zones: raise LoadException(f"Couldn't find `zones` value in Map")
        
        for locName in zones:
            map.addZone(locName)
        for locName in zones:
            data = zones[locName]
            if not data: raise LoadException(f"Couldn't find connections for zone `{locName}` in Map")
            connections = data.split(", ")
            for connection in connections:
                if not map.getZone(connection): LoadException(f"Found invalid connection `{connection}` in `{locName}` in Map")
            map.connectZone(locName, connections)
        
        troves = yaml.get("troves")
        if not troves: troves = {}
        
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
    def eventFromYaml(name: str, data: dict[str, Union[str, dict[str, str]]], processed: dict[str, dict[str, Union[str, dict[str, str]]]]=None, defaultReq: list[list[str]]=None):
        if not processed: processed = {}
        if not defaultReq: defaultReq = []
        
        using: str = data.get("using")
        
        e: object = lambda: 0
        
        # use
        if using:
            if not using in processed:
                raise LoadException(f"`use` value found, but an invalid value was found: `{using}`")
        
        # chance
        chance = data.get("chance")
        if using and not chance: chance = processed[using].get("chance")
        if not chance: raise LoadException(f"`chance` value in event {name} not found")
        if not isinstance(chance, str): raise LoadException(f"`chance` value in event {name} was not a string (got: {chance})")
        
        # text
        text = data.get("text", "")
        if using and not text: text = processed[using].get("text", "")
        if not text: raise LoadException(f"`text` value in event {name} not found")
        if not isinstance(text, str): raise LoadException(f"`text` value in event {name} was not a string (got: {text})")
        text = text.strip()
        
        # req
        req = data.get("req", {})
        if using and not req: req = processed[using].get("req", {})
        if not isinstance(req, dict): raise LoadException(f"`req` value in event {name} was not a dict (got: {req})")
        
        checks = {}
        for charShort in req:
            argsStr = req[charShort]
            if argsStr:
                if not isinstance(argsStr, str): raise LoadException(f"`req` value in event {name} has an argument string ({argsStr}) of the incorrect type")
                checks[charShort] = [*defaultReq, *[spaces.split(allArgs) for allArgs in commas.split(argsStr)]]
            else:
                checks[charShort] = defaultReq
        
        # res
        res = data.get("res", {})
        if using and not res: res = processed[using].get("res", {})
        if not isinstance(res, dict): raise LoadException(f"`res` value in event {name} was not a dict")
        
        effects = {}
        for charShort in res:
            argsStr = res[charShort]
            if argsStr:
                if not isinstance(argsStr, str): raise LoadException(f"`res` value in event {name} has an argument string ({argsStr}) of the incorrect type")
                effects[charShort] = [spaces.split(allArgs) for allArgs in commas.split(argsStr)]
            else:
                effects[charShort] = []
        
        # sub
        sub = data.get("sub", {})
        if using and not sub: sub = processed[using].get("sub", {})
        if not isinstance(sub, dict): raise LoadException(f"`sub` value in event {name} was not a dict")
        
        subEvents = []
        for subName in sub:
            subData = sub[subName]
            subEvents.append(All.eventFromYaml(f"{name}.{subName}", subData, processed, defaultReq))
        
        #print(f"Loading event {name}:\n  chance: {chance}\n  text: {text}\n  checks: {checks}\n  effects: {effects}")
        return Event(name, chance, text, checks, effects, subEvents)
    
    def eventsFromYaml(self, dotsName: str, yaml: dict[str, Union[str, dict[str, Union[str, dict[str, str]]]]]):
        events: dict[str, Event] = {}
        processed: dict[str, Union[str, dict[str, Union[str, dict[str, str]]]]] = {}
        
        defaultReq: list[list[str]] = []
        for name in yaml:
            if name in self.allEvents: raise LoadException(f"Encountered duplicate event {name} in file {dotsName}")
            
            data = yaml[name]
        
            if name.startswith("_DEFAULT"):
                if not type(data) == str:
                    raise LoadException(f"Encountered `_DEFAULT` entry but the value was not a string (got: {data})")
                defaultReq = [spaces.split(allArgs) for allArgs in commas.split(data)]
                continue
                
            event = All.eventFromYaml(name, data, processed, defaultReq)
            processed[name] = data
            events[name] = event
            self.allEvents[name] = event
            
        self.events[dotsName] = events

if __name__ == "__main__":
    all = All("./yamlsources")
    print(all.characters)
    print(all.items)
    print(all.maps)
    print(all.events)
    game = all.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])
    print(game.events)
