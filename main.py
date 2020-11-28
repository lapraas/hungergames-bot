
# id 768553973627224097

from game.All import All

ALL = All("./yamlsources")

GAME = ALL.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])

tributes = []

def doCommand(op, *args):
    global GAME
        
    if op == "trigger":
        if not len(args) == 2:
            print("requires 2 args")
            return False
        eventName, charName = args
        result = GAME.triggerByName(charName, eventName)
        if type(result) == str:
            print(result)
            return
        print(result.getTexts)
        print(result.getEffects)
    
    elif op == "alliesof":
        if not len(args) == 1:
            print("requires 1 arg")
            return False
        tribute = GAME.getTributeByName(args[0])
        print(tribute.alliance)
    
    elif op == "itemsof":
        if not len(args) == 1:
            print("requires 1 arg")
            return False
        tribute = GAME.getTributeByName(args[0])
        print(tribute.items)
    
    elif op == "locationof":
        if not len(args) == 1:
            print("requires 1 arg")
            return False
        tribute = GAME.getTributeByName(args[0])
        print(tribute.location.name)
    
    elif op == "give":
        if not len(args) == 2:
            print("requires 2 or more args")
            return False
        charName, itemName = args
        tribute = GAME.getTributeByName(charName)
        item = GAME.getItemByName(itemName)
        tribute.copyAndGiveItem(item)
        
    elif op == "quit":
        return True

    else:
        print("unrecognized command")
        return False
stop = False

while not stop:
    inp = input("> ")
    inp = inp.split(" ", 1)
    if len(inp) == 0:
        print("enter a command")
    op = inp[0]
    args = []
    if len(inp) == 2:
        args = inp[1].split(", ")
    res = doCommand(op, *args)
    if res: stop = True
