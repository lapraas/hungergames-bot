
from __future__ import annotations
import inflect
p = inflect.engine()

class Item:
    def __init__(self, name: str, tags: list[str]):
        self.name = name
        self.tags = tags
    
    def __repr__(self):
        return f"Item {self.name}"
    
    def __str__(self):
        return self.string()
    
    def string(self, tag: str=None) -> str:
        toRet = self.name
        if tag:
            lcTag = tag.lower()
            if lcTag == "a":
                toRet = p.a(self.name)
            elif tag:
                return None
            if tag[0].isupper():
                toRet = toRet.capitalize()
        return toRet
        
    def hasTag(self, tag: str) -> bool:
        if tag == "ANY":
            return True
        return tag in self.tags
    
    def hasAllTags(self, tags: list[str]) -> bool:
        return all([self.hasTag(tag) for tag in tags])
    
    def copy(self) -> Item:
        return Item(self.name, self.tags)
    
    def getTagsStr(self):
        if not self.tags: return "No tags"
        return ", ".join(self.tags)

def buildItemsFromYaml(yaml: dict[str, str], *_):
    items = []
    for name in yaml:
        data = yaml[name]
        tags = data.split(" ")
        items.append(Item(name, tags))
    return items
