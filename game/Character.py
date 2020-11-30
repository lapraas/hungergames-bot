
from __future__ import annotations
import inflect
p = inflect.engine()
import re
from typing import Callable, Optional

from game.Item import Item
from game.Map import Zone

class Tag:
    def __init__(self, name: str, lasts: int, forever: bool=False):
        self.name = name
        self.age = lasts
        self.forever = False
    
    def __str__(self):
        return f"Tag {self.name} ({self.age})"
    
    def changeAge(self):
        if self.forever:
            self.age += 1
        else:
            self.age -= 1
    
    def isExpired(self):
        return self.age < 0

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
            #print(f"got bad image url for character {self.string()}")
            pass
        self.subj, self.obj, self.plur1, self.plur2, self.flex, self.plural = pronouns
        
        self.items: list[Item] = []
        self.tags: list[Tag] = []
        self.location: Zone = None
        self.alliance: list[Character] = []
        self.alive: bool = True
        self.age: int = 0
        self.roundsSurvived: int = 0
    
    def __repr__(self):
        return f"Character \"{self.name}\""
    
    def __str__(self):
        return self.string()
    
    def __hash__(self) -> int:
        return hash((
            self.name,
            self.imgSrc,
            self.subj, self.obj, self.plur1, self.plur2, self.flex, self.plural
        ))
    
    def __eq__(self, o: object) -> bool:
        if not type(o) == Character: return False
        return all([
            self.name == o.name,
            self.imgSrc == o.imgSrc,
            self.subj == o.subj, self.obj == o.obj, self.plur1 == o.plur1, self.plur2 == o.plur2, self.flex == o.flex, self.plural == o.plural,
            self.items == o.items,
            self.tags == o.tags,
            self.location == o.location,
            # again including alliance would create an infinite recursion
            self.alive == o.alive
        ])
    
    def reset(self):
        self.items = []
        self.tags = []
        self.location = None
        self.alliance = []
        self.alive = True
        self.age = 0
        self.roundsSurvived = 0
    
    def getName(self):
        return self.name
    
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
                toRet = self.subj + ("'re" if self.plural else "'s")
            elif lcTag == "they've":
                toRet = self.subj + ("'ve" if self.plural else "'s")
            elif lcTag == "they'll":
                toRet = self.subj + "'ll"
            elif lcTag == "weren't":
                toRet = lcTag if self.plural else "wasn't"
            elif lcTag == "aren't":
                toRet = lcTag if self.plural else "isn't"
            elif tag:
                # the tag is a verb to conjugate
                toRet = tag
                if not self.plural:
                    toRet = p.plural(tag)
            if tag == None or tag[0].isupper():
                return toRet.capitalize()
        return toRet
    
    def addTag(self, tag: str, lasts: int=0):
        if self.hasTag(tag): return
        if lasts:
            self.tags.append(Tag(tag, lasts))
        else:
            self.tags.append(Tag(tag, 0, True))
    
    def removeTag(self, tagName: str):
        tag = self.getTag(tagName)
        self.tags.remove(tag)
    
    def getTag(self, tagName: str):
        for tag in self.tags:
            if tag.name == tagName:
                return tag
        return None
    
    def hasTag(self, tagName: str):
        if tagName.startswith("!"):
            return not bool(self.getTag(tagName[1:]))
        return bool(self.getTag(tagName))
    
    def compareTagAge(self, tagName: str, age: int, comp: Callable[[int, int], bool]):
        flip = tagName.startswith("!")
        if flip: tagName = tagName[1:]
        tag = self.getTag(tagName)
        if not tag: return False
        return (not comp(tag.age, age)) if flip else (comp(tag.age, age))
    
    def hasTagOverAge(self, tagName: str, age: int):
        return self.compareTagAge(tagName, age, lambda t, a: t > a)
    
    def hasTagAtAge(self, tagName: str, age: int):
        return self.compareTagAge(tagName, age, lambda t, a: t == a)
    
    def hasTagUnderAge(self, tagName: str, age: int):
        return self.compareTagAge(tagName, age, lambda t, a: t < a)
    
    def isAlive(self):
        return self.alive
    
    def kill(self):
        self.alive = False
    
    def revive(self):
        self.alive = True
    
    def incAge(self):
        self.age += 1
        if self.isAlive():
            self.roundsSurvived += 1
        
        toRemove: list[Tag] = []
        for tag in self.tags:
            tag.changeAge()
            if tag.isExpired():
                toRemove.append(tag)
        for tag in toRemove:
            self.tags.remove(tag)
    
    def getAge(self):
        """ Get the total number of rounds this Character has existed. """
        return self.age
    
    def getRoundsSurvived(self):
        """ Get the total number of rounds this Character has been alive. """
        return self.roundsSurvived
    
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
            if item.getName() == itemName:
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
    
    def move(self, newLocation: Zone):
        self.location = newLocation
    
    def moveRandom(self):
        self.move(self.location.getRandomConnection())
    
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
        return ", ".join([tag.name for tag in self.tags])
    
    def getAllianceStr(self):
        if not self.alliance: return "No alliance"
        return ", ".join([ally.string() for ally in self.alliance])
    
    def getAliveStr(self):
        return "Alive" if self.alive else "Dead"
