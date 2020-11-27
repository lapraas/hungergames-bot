
import re
from typing import Union

from game.Character import Character
from game.Item import Item

class State:
    def __init__(self, charsPool: dict[str, Character]=None, itemsPool: dict[str, Character]=None):
        self.charsPool = charsPool if charsPool else {}
        self.itemsPool = itemsPool if itemsPool else {}
        self.resTexts: list[Union[tuple[Character, str], str]] = []
        self.mainCharShort: str = None
    
    def setChar(self, charShort: str, char: Character):
        self.charsPool[charShort] = char
        if not self.mainCharShort:
            self.mainCharShort = charShort
    
    def setItem(self, itemShort: str, item: Item):
        self.itemsPool[itemShort] = item
    
    def getChar(self, charShort: str):
        if not charShort:
            return self.getChar(self.mainCharShort)
        return self.charsPool[charShort]
    
    def doesCharExist(self, char: Character):
        return char in self.charsPool
    
    def getItem(self, itemShort: str):
        return self.itemsPool[itemShort]
    
    def addResText(self, char: Character, resText: str):
        self.resTexts.append((char, resText))
    
    def getResTexts(self):
        return self.resTexts
    
    def makeNew(self, text: str):
        return State(text, self.charsPool, self.itemsPool)
    
    def addReplacedText(self, text):
        textReplacePat = re.compile(r"([A-Za-z']*)(@|&)(\w+)")
        matches = textReplacePat.finditer(text)
        offset = 0
        for match in matches:
            toConj, objType, short = match.groups()
            replaceObj = None
            if objType == "@":
                replaceObj = self.charsPool[short]
            elif objType == "&":
                replaceObj = self.itemsPool[short]
            replaceText = replaceObj.string(toConj)
            
            text = text[:match.start() - offset] + replaceText + text[match.end() - offset:]
            letterDiff = match.end() - match.start() - len(replaceText)
            offset += letterDiff
        
        return text
    
    def getMainCharacter(self):
        return self.mainCharShort
