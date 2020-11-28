
from random import choice
from typing import Union

from game.Item import Item

class Trove:
    """ A collection of random Items that Events can give Characters. """
    
    def __init__(self, name: str, count: int, pool: list[Union[str, list[str]]], has: list[str]):
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
    
    def reset(self):
        self.pool = []
        self.gen = []
    
    def load(self, loadedItems: list[Item]):
        """ Populates the Trove's generated items. """
        
        for item in loadedItems:
            for tagList in self.tagsPool:
                if type(tagList) == str and tagList.startswith("="):
                    targetName = tagList[1:]
                    if item.getName() == targetName:
                        self.pool.append(item)
                else:
                    if item.hasAllTags(tagList):
                        self.pool.append(item)
            for targetName in self.has:
                if item.getName() == targetName:
                    self.gen.append(item)
        for _ in range(self.count):
            self.gen.append(choice(self.pool))
    
    def takeRandomItem(self):
        """ Gets a random Item from this Trove's generated Items. """
        
        item = choice(self.gen)
        self.gen.remove(item)
        return item
