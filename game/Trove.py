
from random import choice
from typing import Union

from game.Item import Item

class Trove:
    """ A collection of random Items that Events can give Characters. """
    
    def __init__(self, name: str, count: int, pool: list[list[str]], has: list[str]):
        self.name = name
        # Number of items total in the Trove (not including guaranteed items)
        self.count = count
        # A list of item tags or specific item names (prepended with "=") for items which can be generated
        self.tagsPool = pool
        # Guaranteed items (specific items)
        self.has = has
        # A list of Items which can be generated
        self.pool: list[Item] = []
        # A list of Items which have been generated
        self.gen: list[Item] = []
    
    def getName(self):
        return self.name
    
    def reset(self):
        """ Resets the Trove's generated items. """
        self.pool = []
        self.gen = []
    
    def load(self, loadedItems: dict[str, Item]):
        """ Populates the Trove's generated items. """
        
        for tagList in self.tagsPool:
            if tagList[0].startswith("="):
                targetName = tagList[0][1:]
                item = loadedItems.get(targetName)
                if not item: raise Exception(f"Encountered invalid specific item name in Trove \"{self.name}\"'s pool: \"{targetName}\"")
                self.pool.append(item.copy())
            for item in loadedItems.values():
                if item.hasAllTags(tagList):
                    self.pool.append(item.copy())
        
        for targetName in self.has:
            item = loadedItems.get(targetName)
            if not item: raise Exception(f"Encountered invalid specific item name in Trove \"{self.name}\"'s guaranteed items: \"{targetName}\"")
            self.gen.append(item.copy())
        
        for _ in range(self.count):
            self.gen.append(choice(self.pool))
    
    def hasItems(self):
        return len(self.gen) > 0
    
    def loot(self):
        """ Gets a random Item from this Trove's generated Items. """
        
        item = choice(self.gen)
        self.gen.remove(item)
        return item
