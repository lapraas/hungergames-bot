
from __future__ import annotations
import inflect
p = inflect.engine()
import re

from typing import Optional
from game.Item import Item
from game.Map import Zone

def _match_url(url):
    regex = re.compile(
        "(([\w]+:)?//)?(([\d\w]|%[a-fA-f\d]{2,2})+(:([\d\w]|%[a-fA-f\d]{2,2})+)?@)?([\d\w][-\d\w]{0,253}[\d\w]\.)+[\w]{2,63}(:[\d]+)?(/([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)*(\?(&?([-+_~.\d\w]|%[a-fA-f\d]{2,2})=?)*)?(#([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)?"
    ) # this monstrosity was stolen from stackexchange https://stackoverflow.com/questions/58211619/how-to-check-for-hyperlinks-in-the-contents-of-a-message-through-discord-py-pre
    if regex.match(url):
        return True
    else:
        return False
        
class Character:
    def __init__(self, name: str, imgSrc: str, pronouns: tuple[str, str, str, str, bool]):
        self.name = name
        self.imgSrc = imgSrc if _match_url(imgSrc) else None
        if not self.imgSrc:
            print(f"got bad image url for character {self.string()}")
        self.subj, self.obj, self.plur1, self.plur2, self.flex, self.plural = pronouns
        
        self.items: list[Item] = []
        self.tags: list[str] = []
        self.location: Zone = None
        self.alliance: list[Character] = []
        self.alive: bool = True
    
    def __repr__(self):
        return f"Character {self.name}"
    
    def __str__(self):
        return self.string()
    
    def reset(self):
        self.items = []
        self.tags = []
        self.location = None
        self.alliance = []
        self.alive = True
    
    def getPicture(self):
        return self.imgSrc
        
    def string(self, tag: str = None) -> str:
        toRet = self.name
        if tag:
            lcTag = tag.lower()
            if lcTag == "they":
                toRet = self.subj
            elif lcTag == "them":
                toRet = self.obj
            elif lcTag == "their":
                toRet = self.plur1
            elif lcTag == "theirs":
                toRet = self.plur2
            elif lcTag == "themself":
                toRet = self.flex
            elif lcTag == "they're":
                toRet = self.subj + "'re"
                if not self.plural:
                    toRet = self.subj + "'s"
            elif tag:
                # the tag is a verb to conjugate
                toRet = tag
                if not self.plural:
                    toRet = p.plural(tag)
            if tag == None or tag[0].isupper():
                return toRet.capitalize()
        return toRet
    
    def addTag(self, tag: str):
        self.tags.append(tag)
    
    def removeTag(self, tag: str):
        self.tags.remove(tag)
    
    def hasTag(self, tag: str):
        return tag in self.tags
    
    def isAlive(self):
        return self.alive
    
    def kill(self):
        self.alive = False
    
    def revive(self):
        self.alive = True
    
    def copyAndGiveItem(self, item: Item):
        copy = item.copy()
        self.items.append(copy)
    
    def getItemByTags(self, tags: list[str]) -> Optional[Item]:
        for item in self.items:
            if item.hasAllTags(tags):
                return item
        return None
    
    def getItemByName(self, itemName: str) -> Optional[Item]:
        for item in self.items:
            if item.string() == itemName:
                return item
        return None
    
    def takeItem(self, item: Item):
        self.items.remove(item)
    
    def getLocation(self) -> Zone:
        return self.location
    
    def isIn(self, loc: str) -> bool:
        return self.location.name == loc
    
    def isNearby(self, other: Character):
        return self.getLocation() == other.getLocation()
    
    def move(self, newLocation: str):
        self.location = newLocation
        if self.hasTag("running"):
            self.removeTag("running")
    
    def moveRandom(self):
        self.move(self.location.getRandomConnx())
    
    def isAlone(self):
        return len(self.alliance) == 0
    
    def getAlliance(self):
        return self.alliance
    
    def joinAlliance(self, alliance: list[Character]):
        self.alliance = alliance
        self.alliance.append(self)
    
    def leaveAlliance(self):
        if self.isAlone(): return
        self.alliance.remove(self)
        self.alliance = []
        
    def isAllyOf(self, other: Character):
        return other in self.alliance
    
    def getLocationStr(self):
        if not self.location: return "No location"
        return self.location.name
    
    def getItemsStr(self):
        if not self.items: return "No items"
        return ", ".join([item.string() for item in self.items]).capitalize()
    
    def getTagsStr(self):
        if not self.tags: return "No tags"
        return ", ".join(self.tags).capitalize()
    
    def getAllianceStr(self):
        if not self.alliance: return "No alliance"
        return ", ".join([ally.string() for ally in self.alliance])
    
    def getAliveStr(self):
        return "Alive" if self.alive else "Dead"

def buildCharactersFromYaml(yaml: dict[str, tuple[str, str]], *_):
    chars = []
    for name in yaml:
        data = yaml[name]
        if not len(data) >= 2:
            raise Exception(f"Couldn't load character {name}, too few elements in list ({data})")
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
    return chars
