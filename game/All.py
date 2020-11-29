
from re import L
from game.Trove import Trove
from game.Game import Game
from game.Valids import Valids
import os
import re
from typing import Any, Callable, Union

from ruamel.yaml import YAML
yaml = YAML()

from game.Character import Character
from game.Event import Event
from game.Item import Item
from game.Map import Map

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
    
    def loadGameWithSettings(self, characterFiles: list[str], itemFiles: list[str], mapFile: str, eventFiles: list[str]):
        loadedCharacters: dict[str, Character] = self.load(characterFiles, self.characters, self.allCharacters)
        loadedItems: dict[str, Item] = self.load(itemFiles, self.items, self.allItems)
        loadedMap: Map = self.loadOne(mapFile, self.maps)
        loadedEvents: dict[str, Event] = self.load(eventFiles, self.events, self.allEvents)
        
        loadedMap.loadTroves(loadedItems)
        for event in loadedEvents.values():
            valids = Valids(loadedMap, loadedItems)
            event.load(valids)
        
        return Game(loadedItems, loadedEvents, loadedCharacters, loadedMap)
    
    def load(self, files: str, objsPerFile: dict[str, dict[str, Any]], allObjs: dict[str, Any]) -> dict[str, Any]:
        loaded = {}
        for file in files:
            if file == "ALL":
                loaded = allObjs
                break
            toLoad = objsPerFile.get(file)
            loaded = {**loaded, **toLoad}
        return loaded
    
    def loadOne(self, file, objDict: dict[str, object]) -> Any:
        toLoad = objDict.get(file)
        return toLoad
    
    def dotPathToReal(self, dirName: str, dotPath: str):
        path = os.path.join(self.rootPath, dirName, *dotPath.split("."))
        return path + ".yaml"
    
    def getYamlFromFile(self, filename: str):
        with open(filename, "r") as f:
            allYaml = yaml.load(f)
            if not allYaml: allYaml = {}
            return allYaml
    
    def replaceYamlInFile(self, filename: str, allYaml: str):
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
            allYaml = self.getYamlFromFile(os.path.join(path, file))
            try:
                buildFun(dotsName, allYaml)
            except LoadException as e:
                raise LoadException(f"In file {baseDotsName}: {e}")
        
        for subdir in subdirs:
            fullPath = os.path.join(dirName, subdir)
            self.build(buildFun, fullPath, subdir)
        
    def create(self, name: str, data: Any, buildFun: Callable[[str, Any], Any], objsPerFile: dict[str, dict[str, Any]], allObjs: dict[str, Any], dotFileName):
        if not dotFileName in objsPerFile: raise LoadException(f"Couldn't find a file at {dotFileName}")
        if name in allObjs: raise LoadException(f"Tried to create duplicate \"{name}\"")
        
        targetFilePath = self.dotPathToReal(self.charsDirName, dotFileName)
        allYaml = self.getYamlFromFile(targetFilePath)
        
        new = buildFun(name, data)
        allYaml[name] = data
        self.replaceYamlInFile(targetFilePath, allYaml)
        
        objsPerFile[dotFileName][name] = new
        allObjs[name] = new
    
    ###
    # Character
    ###
    
    def characterFromYaml(self, name: str, data: tuple[str, str]):
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
            char = self.characterFromYaml(name, data)
            chars[name] = char
            self.allCharacters[name] = char
        
        self.characters[dotsName] = chars
    
    def addCharacter(self, name: str, data: tuple[str, str], dotFileName="adds"):
        self.create(name, data, self.characterFromYaml, self.characters, self.allCharacters, dotFileName)
    
    ###
    # Item
    ###
    
    def itemFromYaml(self, name: str, data: str):
        return Item(name, data.split(" "))
    
    def itemsFromYaml(self, dotsName: str, yaml: dict[str, str]):
        items: dict[str, Item] = {}
        
        for name in yaml:
            if name in self.allItems: raise LoadException(f"Encountered duplicate Item {name} in file {dotsName}")
            
            data = yaml[name]
            item = self.itemFromYaml(name, data)
            items[name] = item
            self.allItems[name] = item
        
        self.items[dotsName] = items
    
    def addItem(self, name: str, data: str, dotFileName="adds"):
        self.create(name, data, self.itemFromYaml, self.items, self.allItems, dotFileName)
    
    ###
    # Map
    ###
    
    def mapFromYaml(self, dotsName: str, yaml: dict[str, dict[str, Union[str, dict[str, Union[str, int]]]]]):
        map = Map()
        zones = yaml.get("zones")
        if not zones: raise LoadException(f"Couldn't find \"zones\" value in Map")
        
        for locName in zones:
            map.addZone(locName)
        for locName in zones:
            data = zones[locName]
            if not data: raise LoadException(f"Couldn't find connections for zone \"{locName}\" in Map")
            connections = data.split(", ")
            for connection in connections:
                if not map.getZone(connection): LoadException(f"Found invalid connection \"{connection}\" in \"{locName}\" in Map")
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
            if not (pool or has): raise LoadException(f"Trove requires either \"pool\" or \"has\" values, neither were found in Trove \"{troveName}\"")
            if pool:
                pool = commas.split(pool)
                pool = [spaces.split(tags) for tags in pool]
                for tags in pool:
                    if tags[0] == "": raise LoadException(f"Got an empty \"pool\" tag list entry")
            if has:
                has = commas.split(has)
            trove = Trove(troveName, count, pool, has)
            map.addTrove(trove)
        
        self.maps[dotsName] = map
    
    ###
    # Event
    ###
    
    def eventFromYaml(self, name: str, data: Union[str, dict[str, Union[str, dict[str, str]]]], defaultReq: list[list[str]]=[]):
        if name == "DEFAULT":
            if not type(data) == str:
                raise LoadException(f"Encountered DEFAULT entry by the value ({data}) was not a string")
            return [spaces.split(allArgs) for allArgs in commas.split(data)]
        chance = data.get("chance")
        if not chance: raise LoadException(f"\"chance\" value in event {name} not found")
        
        text = data.get("text")
        if not text: raise LoadException(f"\"text\" value in event {name} not found")
        text = text.strip()
        
        checks = data.get("req")
        if not checks: checks = {}
        if type(checks) == str: raise LoadException(f"\"req\" value in event {name} was a string (\"{checks}\"), needs to be a dict")
        
        for charShort in checks:
            argsStr = checks[charShort]
            if argsStr:
                if not type(argsStr) == str: raise LoadException(f"\"req\" value in event {name} has an argument string ({argsStr}) of the incorrect type")
                checks[charShort] = [*defaultReq, *[spaces.split(allArgs) for allArgs in commas.split(argsStr)]]
            else:
                checks[charShort] = defaultReq
        
        effects = data.get("res")
        if not effects: effects = {}
        if type(effects) == str: raise LoadException(f"\"res\" value in event {name} was a string (\"{effects}\"), needs to be a dict")
        
        for charShort in effects:
            argsStr = effects[charShort]
            if argsStr:
                if not type(argsStr) == str: raise LoadException(f"\"res\" value in event {name} has an argument string ({argsStr}) of the incorrect type")
                effects[charShort] = [spaces.split(allArgs) for allArgs in commas.split(argsStr)]
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
        events: dict[str, Event] = {}
        
        defaultReq: list[list[str]] = []
        for name in yaml:
            if name in self.events: raise LoadException(f"Encountered duplicate event {name} in file {dotsName}")
            
            data = yaml[name]
            event = self.eventFromYaml(name, data, defaultReq)
            if type(event) != Event:
                defaultReq = event
                continue
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
