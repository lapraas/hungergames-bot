
from ruamel.yaml import events
from game.Game import Game
from game.Valids import Valids
import os
import re
from typing import Callable

from ruamel.yaml import YAML
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
        
        self.charsDirName = charsDirName
        self.characters: dict[str, list[Character]] = {}
        self.allCharacters: list[Character] = []
        res = self.build(self.charactersFromYaml, self.charsDirName)
        if res: raise LoadException(res)
        
        self.itemsDirName = itemsDirName
        self.items: dict[str, list[Item]] = {}
        self.allItems: list[Item] = []
        res = self.build(self.itemsFromYaml, self.itemsDirName)
        if res: raise LoadException(res)
        
        self.mapsDirName = mapsDirName
        self.maps: dict[str, Map] = {}
        self.allMaps: list[Map] = []
        res = self.build(self.mapFromYaml, self.mapsDirName)
        if res: raise LoadException(res)
        
        self.eventsDirName = eventsDirName
        self.events: dict[str, list[Event]] = {}
        self.allEvents: list[Event] = []
        res = self.build(self.eventsFromYaml, self.eventsDirName)
        if res: raise LoadException(res)
    
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
    
    def characterFromYaml(self, name: str, data: tuple[str, str]):
        if not len(data) >= 2:
            return f"Couldn't load character {name}, too few elements in list ({data})"
        
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
                return f"Couldn't load Character {name}, there were not 6 values for the Character's pronouns ({pronouns})"
            pronouns[5] = True if not pronouns[5] in ["False", "0"] else False
        
        imgSrc = data[1]
        return Character(name, imgSrc, pronouns)
    
    def charactersFromYaml(self, dotsName: str, yaml: dict[str, list[str]]):
        chars = []
        for name in yaml:
            data = yaml[name]
            res = self.characterFromYaml(name, data)
            if type(res) == str:
                return res
            chars.append(res)
        
        self.characters[dotsName] = chars
        self.allCharacters += chars
    
    def addCharacter(self, name: str, data: tuple[str, str], dotFileName="adds"):
        if not dotFileName in self.characters:
            return f"Couldn't find a file at {dotFileName}"
        
        newCharacter = self.characterFromYaml(name, data)
        if type(newCharacter) == str:
            return newCharacter
        
        targetFilePath = self.dotPathToReal(self.charsDirName, dotFileName)
        allYaml = self.getYamlFromFile(targetFilePath)
        allYaml[name] = data
        self.replaceYamlInFile(targetFilePath, allYaml)
        
        self.characters[dotFileName].append(newCharacter)
        self.allCharacters.append(newCharacter)
    
    def itemFromYaml(self, name: str, data: str):
        return Item(name, data.split(" "))
    
    def itemsFromYaml(self, dotsName: str, yaml: dict[str, str]):
        items = []
        for name in yaml:
            data = yaml[name]
            items.append(self.itemFromYaml(name, data))
        
        self.items[dotsName] = items
        self.allItems += items
    
    def addItem(self, name: str, data: str, dotFileName="adds"):
        if not dotFileName in self.items:
            return False
        targetFilePath = self.dotPathToReal(self.itemsDirName, dotFileName)
        allYaml = self.getYamlFromFile(targetFilePath)
        
        newItem = self.itemFromYaml(name, data)
        if type(newItem) == str:
            return newItem
        allYaml[name] = data
        self.replaceYamlInFile(targetFilePath, allYaml)
        
        self.items[dotFileName].append(newItem)
        self.allItems.append(newItem)
    
    def mapFromYaml(self, dotsName: str, yaml: dict[str, list[dict[str, str]]]):
        map = Map()
        zones = yaml.get("zones")
        if not zones: return f"Couldn't find \"zones\" value in Map"
        
        for loc in zones:
            name = loc.get("name")
            if not name: return f"Couldn't find name for zone in Map"
            map.addZone(name)
        for loc in zones:
            name = loc["name"]
            connx = loc["connx"]
            if not connx: return f"Couldn't find connx for zone {name} in map"
            map.connectZone(name, connx.split(" "))
        
        self.maps[dotsName] = map
        self.allMaps.append(map)
    
    def eventFromYaml(self, name: str, data: dict[str, dict[str, str]]):
        chance = data.get("chance")
        if not chance: return f"\"chance\" value in event {name} not found"
        
        text = data.get("text")
        if not text: return f"\"text\" value in event {name} not found"
        
        checks = data.get("checks")
        if not checks: checks = {}
        if type(checks) == str: return f"\"checks\" value in event {name} was a string (\"{checks}\"), needs to be a dict"
        
        for charShort in checks:
            argsStr = checks[charShort]
            if argsStr:
                if not type(argsStr) == str: return f"\"checks\" value in event {name} has an argument string ({argsStr}) of the incorrect type"
                checks[charShort] = [spacePat.split(allArgs) for allArgs in commaPat.split(argsStr)]
            else:
                checks[charShort] = []
        
        effects = data.get("effects")
        if not effects: effects = {}
        if type(effects) == str: return f"\"effects\" value in event {name} was a string (\"{effects}\"), needs to be a dict"
        
        for charShort in effects:
            argsStr = effects[charShort]
            if argsStr:
                if not type(argsStr) == str: return f"\"effects\" value in event {name} has an argument string ({argsStr}) of the incorrect type"
                effects[charShort] = [spacePat.split(allArgs) for allArgs in commaPat.split(argsStr)]
            else:
                effects[charShort] = []
        
        sub = data.get("sub")
        if not sub: sub = {}
        subEvents = []
        for subName in sub:
            subData = sub[subName]
            res = self.eventFromYaml(subName, subData)
            if type(res) == str: return res
            subEvents.append(res)
        
        return Event(name, chance, text, checks, effects, subEvents)
    
    def eventsFromYaml(self, dotsName: str, yaml: dict[str, dict[str, dict[str, str]]]):
        events: list[Event] = []
        for name in yaml:
            data = yaml[name]
            res = self.eventFromYaml(name, data)
            if type(res) == str: return res
            events.append(res)
            
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
                if not allYaml: allYaml = {}
                res = buildFun(dotsName, allYaml)
                if res:
                    return res + f" (in file {dotsName})"
        
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
