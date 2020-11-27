
import os
from typing import Callable, Optional

from ruamel.yaml import YAML
yaml = YAML()

from game.Character import buildCharactersFromYaml
from game.Event import buildEventsFromYaml
from game.Game import Game
from game.Item import buildItemsFromYaml
from game.Map import buildMapFromYaml, buildZoneEventPaths

def loadAll(path: str, fileNames: Optional[list[str]], buildFun: Callable, args: list=None):
    dex: list = []
    for fileName in os.listdir(path):
        if fileNames and not fileName in fileNames and not "ALL" in fileNames: continue
        try:
            objList = load(f"{path}/{fileName}", buildFun, args)
        except Exception as e:
            raise Exception(f"Error loading file \"{fileName}\", {e}")
        if objList == None: continue
        print(f"loaded {objList}")
        dex += objList
    return dex

def load(path: str, buildFun: Callable, args: list=None):
    if not args:
        args = []
    with open(path, "r") as f:
        yamlObj = yaml.load(f)
        if not yamlObj: return None
        return buildFun(yamlObj, *args)

def add(path: str, name, obj = dict):
    f = open(path, "r")
    allYaml = yaml.load(f)
    f.close()
    
    if not allYaml:
        allYaml = {}
    
    allYaml[name] = obj
    
    with open(path, "w") as f:
        yaml.dump(allYaml, f)

def loadFromSetup(setup: dict[str, str]):
    mapFName = setup["map"]
    charsFNames = setup["characters"].split(" ")
    eventsFNames = setup["events"].split(" ")
    itemsFNames = setup["items"].split(" ")
    
    map = load(f"./yamlsources/maps/{mapFName}", buildMapFromYaml)
    eventsFNames += load(f"./yamlsources/maps/{mapFName}", buildZoneEventPaths)
    chars = loadAll("./yamlsources/characters", charsFNames, buildCharactersFromYaml)
    items = loadAll("./yamlsources/items", itemsFNames, buildItemsFromYaml)
    events = loadAll("./yamlsources/events", eventsFNames, buildEventsFromYaml, [items, map])
    
    return Game(items, events, chars, map)

def defaultLoad() -> Game:
    return load("./yamlsources/setup.yaml", loadFromSetup)
