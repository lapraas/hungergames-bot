
from os import stat

from discord.errors import NotFound
from game.State import Result
from typing import Any, Callable, KeysView, Optional, TypeVar
from discord.embeds import Embed
from discord.ext import commands
from discord import Forbidden
from discord.ext.commands.context import Context

from game.Character import Character
from game.All import All, LoadException
#ALL = All("./yamlsources")
ALL = All("./mysterydungeon", charsDirName="../yamlsources/characters")

EVENTGREEN = 0xbbff45
CHARINFOBLUE = 0x2c32db
MISCORANGE = 0xff9e1f
ERRORRED = 0xe30f00
BORDERBLACK = 0x000000

class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.charactersSet = [""]
        self.itemsSet = [""]
        self.mapSet = "simple"
        self.eventsSet = [""]
        self.game = self.getNewGame()
        
    ###
    # Utility things
    ###
    
    def getNewGame(self):
        return ALL.loadGameWithSettings(
            self.charactersSet,
            self.itemsSet,
            self.mapSet,
            self.eventsSet
        )
    
    @staticmethod
    def getErrorEmbed(title, description=None):
        """ Gets a basic error embed. """
        return Embed(
            title = title,
            description = description,
            color = ERRORRED
        )
    
    @staticmethod
    async def checkArgs(ctx: Context, args: list[str], argNames: list[str]) -> Optional[list[str]]:
        """ Remakes the arguments to be comma-separated rather than space-separated.
            Checks the number of args to make sure it matches what's expected.
            If it's not what's expected, send an error embed to the Context and return None.
            Otherwise returns the arguments. """
        
        realArgs = [s.strip() for s in " ".join(args).split(",")]
        argNamesStr = ", ".join(argNames)
        if len(realArgs) == len(argNames):
            return realArgs
        
        await ctx.send(embed=MainCog.getErrorEmbed(f"This command needs {len(argNames)} arguments ({argNamesStr}), {len(realArgs)} recieved. Args are comma-separated."))
    
    @staticmethod
    def getCharEmbed(char: Character, title="", description="", color=MISCORANGE) -> Embed:
        """ Initializes an Embed based on the given Character.
            Defaults to making the title the .string() of the Character,
            making the description empty,
            and making the color orange. """
        
        embed = Embed(title=char.string() if not title else title, description=description, color=color)
        url = char.getPicture()
        if url:
            embed.set_thumbnail(url=url)
        return embed
    
    @staticmethod
    def getResultEmbed(mc: Character, result: Result) -> Embed:
        """ Returns an Embed based on the Result object given by a triggered Event. """
        
        text = "\n\n".join(result.getTexts())
        embed = MainCog.getCharEmbed(mc, "Event", text, EVENTGREEN)
        effects = result.getEffects()
        for char in effects:
            resText = "\n".join(effects[char])
            embed.add_field(name=char.string(), value=resText)
        
        return embed
    
    async def getSingleCharacter(self, ctx: Context, args: str) -> Optional[Character]:
        """ Attempts to get a loaded Character from the game based on the given args.
            If unsuccessful, sends an error embed to the given Context and returns None,
            otherwise returns the Character. """
        
        args = await MainCog.checkArgs(ctx, args, ["character name"])
        if not args: return None
        charName, = args
        char = self.game.getTributeByName(charName)
        if not char:
            embed = Embed(
                title=f"Couldn't find a character named {charName}",
                color=ERRORRED
            )
            await ctx.send(embed=embed)
            return None
        return char
    
    @staticmethod
    def getExceptionEmbed(title: str, e: Exception) -> Embed:
        """ A special Embed creator for Exceptions. """
        return MainCog.getErrorEmbed(title, f"Encountered error:\n\n{e}")
    
    @staticmethod
    def wrapAddCall(fun: Callable, callTitle: str, callDesc: str) -> Embed:
        """ Catches LoadExceptions when trying to add things to ALL. """
        try:
            fun()
        except LoadException as e:
            return MainCog.getExceptionEmbed(callTitle, e)
            
        return Embed(
            title = callTitle,
            description = callDesc,
            color = MISCORANGE
        )
    
    @staticmethod
    def buildListEmbed(title: str, sorteds: tuple[str, Any], valueFun: Callable[[Any], str], inline: bool=True):
        """ Builds an embed with a list of game objects. Used by the .list commands. """
        embeds = []
        for x in range(int(len(sorteds) / 25)+1):
            n = x * 25
            embed = Embed(title=title, color=MISCORANGE)
            for name, obj in sorteds[n:n+25]:
                embed.add_field(name=name, value=valueFun(obj), inline=inline)
            embeds.append(embed)
        
        return embeds
    
    @staticmethod
    def buildSingleListEmbed(title: str, sorteds: tuple[str, Any], valueFun: Callable[[Any], str]):
        embedStr = "\n".join([f"{name}: {valueFun(obj)}" for name, obj in sorteds])
        return Embed(title=title, description=embedStr, color=MISCORANGE)
    
    ############
    # Commands #
    ############
    
    @commands.command()
    async def ping(self, ctx: Context):
        """ Test command. """
        await ctx.send("Pong!")
    
    @commands.command(aliases=["help"])
    async def listcommands(self, ctx: Context):
        """ Lists all commands. """
        
        embed = Embed(
            title = "All commands:",
            color = MISCORANGE
        )
        for command in ctx.bot.commands:
            embed.add_field(name=command.name, value=command.help, inline=False)
        
        await ctx.send(embed=embed)
    
    #
    # Adds
    #
    
    @commands.command()
    async def addchar(self, ctx: Context, *args: str):
        """ Adds a Character to the game. Takes a name, a gender or space-separated list of pronouns, and a portrait URL. """
        
        args = await MainCog.checkArgs(ctx, args, ["name", "gender/pronouns", "portrait URL"])
        if not args: return
        charName, charGender, charURL = args
        
        await ctx.send(embed=MainCog.wrapAddCall(
            lambda: ALL.addCharacter(charName, [charGender, charURL]),
            "Add Character",
            f"Added character {charName} with gender {charGender} and image URL {charURL}"
        ))
    
    @commands.command()
    async def additem(self, ctx: Context, *args: str):
        """ Adds an Item to the game. Takes a name and a space-separated list of tags."""
        
        args = await MainCog.checkArgs(ctx, args, ["name", "tags"])
        if not args: return
        itemName, itemTags = args[:2]
        
        await ctx.send(embed=MainCog.wrapAddCall(
            lambda: ALL.addItem(itemName, itemTags),
            "Add Item",
            f"Added item {itemName} with tags {itemTags}"
        ))
    
    #
    # Game execution
    #
    
    @commands.command()
    async def load(self, ctx: Context, *args: str):
        """ Reloads the game using the given load settings. """
        args = await self.checkArgs(ctx, args, ["Character settings", "Item settings", "Map setting", "Event settings"])
        if not args: return
        
        try:
            self.charactersSet = [a.strip() for a in args[0].split(" ")]
            self.itemsSet = [a.strip() for a in args[1].split(" ")]
            self.mapSet = args[2].strip()
            self.eventsSet = [a.strip() for a in args[3].split(" ")]
            
            self.game = self.getNewGame()
        except Exception as e:
            await ctx.send(embed=MainCog.getExceptionEmbed("Loading new game", e))
            return
            
        await ctx.send("Reloaded game.")
    
    @commands.command()
    async def start(self, ctx: Context):
        """ Starts the game if it hasn't already been started. """
        res = self.game.start()
        if not res:
            await ctx.send(embed=self.getErrorEmbed("Game was already started."))
            return
        else:
            await ctx.send(embed=Embed(
                title="The games are about to begin.",
                description=self.game.getRoundFlavor(),
                color=BORDERBLACK
            ))
        await ctx.send(embed=Embed(
            title="Round start!",
            description="Use .next to progress a round.",
            color=BORDERBLACK
        ))
    
    @commands.command()
    async def next(self, ctx: Context):
        """ Progresses a round if one is happening. """
        try:
            await ctx.message.delete()
        except (Forbidden, NotFound):
            pass
        
        res = self.game.next()
        if res == None:
            return self.next()
        if res == False:
            await ctx.send(embed=MainCog.getErrorEmbed("The game hasn't been started. Use .start to start it."))
            return True
        await ctx.send(embed=MainCog.getResultEmbed(res.getMainChar(), res))
        
        if self.game.isRoundGoing(): return True
        
        flavor = self.game.getRoundFlavor()
        await ctx.send(embed=Embed(
            title="Round end!",
            description=flavor,
            color=BORDERBLACK
        ))
        await self.remaining(ctx)
        return False
    
    @commands.command()
    async def nextall(self, ctx: Context):
        """ Uses the `next` command until the round is over. """
        
        res = await self.next(ctx)
        while res:
            res = await self.next(ctx)
    
    @commands.command()
    async def remaining(self, ctx: Context):
        """ Gives the number of remaining tributes. """
        

    #
    # Game debugging
    #
    
    @commands.command()
    async def trigger(self, ctx: Context, *args: str):
        """ Triggers an Event. Takes the name of a loaded Character and the name of a loaded Event. """
        
        args = await MainCog.checkArgs(ctx, args, ["character name", "event name"])
        if not args: return
        charName, eventName = args
        
        result = self.game.triggerByName(charName, eventName)
        char = self.game.getTributeByName(charName)
        
        await ctx.send(embed=MainCog.getResultEmbed(char, result))
    
    @commands.command()
    async def give(self, ctx: Context, *args: str):
        """ Adds an Item to a Character's inventory. Takes the name of a loaded Character and the name of a loaded Item. """
        
        args = await MainCog.checkArgs(ctx, args, ["character name", "item name"])
        if not args: return
        charName, itemName = args
        tribute = self.game.getTributeByName(charName)
        if not tribute:
            await ctx.send(f"Couldn't find character named {charName}")
            return
        item = self.game.getItemByName(itemName)
        if not item:
            await ctx.send(f"Couldn't find item named {itemName}")
            return
        tribute.copyAndGiveItem(item)
        await ctx.send(f"Gave {item} to {tribute}")
    
    @commands.command()
    async def charinfo(self, ctx: Context, *args: str):
        """ Gets the current state of a Character. Takes the name of a loaded Character. """
        
        char = await self.getSingleCharacter(ctx, args)
        if not char: return
        
        embed = MainCog.getCharEmbed(char, color=CHARINFOBLUE)
        embed.add_field(name="Location:", value=char.getLocationStr())
        embed.add_field(name="Items:", value=char.getItemsStr())
        embed.add_field(name="Tags:", value=char.getTagsStr())
        embed.add_field(name="Alliance:", value=char.getAllianceStr())
        embed.add_field(name="Status:", value=char.getAliveStr())
        
        url = char.getPicture()
        if url:
            embed.set_thumbnail(url=url)
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["loadedevents"])
    async def listevents(self, ctx: Context):
        """ Lists all Events currently loaded in the game. """
        
        await ctx.send(embed=MainCog.buildSingleListEmbed(
                "Loaded Events:",
                self.game.getSortedEvents(),
                lambda event: event.getChance()
        ))
    
    @commands.command(aliases=["loadeditems"])
    async def listitems(self, ctx: Context):
        """ Lists all Items currently loaded in the game. """
        
        for embed in MainCog.buildListEmbed(
                "Loaded Items:",
                self.game.getSortedItems(),
                lambda item: item.getTagsStr()
            ):
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["loadedzones"])
    async def listzones(self, ctx: Context):
        """ Lists all Zones loaded in the game. """
        
        for embed in MainCog.buildListEmbed(
                "Loaded Zones:",
                self.game.getSortedZones(),
                lambda zone: zone.getConnectionsStr(),
                False
            ):
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["loadedchars"])
    async def listchars(self, ctx: Context):
        """ Lists all Characters loaded in the game. """
        
        for embed in MainCog.buildListEmbed(
                "Loaded Characters:",
                self.game.getSortedTributes(),
                lambda char: char.getAliveStr()
            ):
            await ctx.send(embed=embed)
    