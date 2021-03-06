
from __future__ import annotations
import inflect
p = inflect.engine()

class Item:
    def __init__(self, name: str, tags: list[str]):
        self.name = name
        self.tags = tags
    
    def __repr__(self):
        return f"Item \"{self.name}\""
    
    def __str__(self):
        return self.string()
    
    def getName(self):
        return self.name
    
    def string(self, tag: str=None) -> str:
        toRet = self.name
        if tag:
            lcTag = tag.lower()
            if lcTag == "a":
                toRet = p.a(self.name)
            elif tag:
                return None
        return toRet
        
    def hasTag(self, tag: str) -> bool:
        if "SECRET" in self.tags:
            return tag == "SECRET"
        if tag == "ANY":
            return True
        return tag in self.tags
    
    def hasAllTags(self, tags: list[str]) -> bool:
        if "ANY" in tags: return True
        return all([self.hasTag(tag) for tag in tags])
    
    def copy(self) -> Item:
        return Item(self.name, self.tags)
    
    def getTagsStr(self):
        if not self.tags: return "No tags"
        return ", ".join(self.tags)
