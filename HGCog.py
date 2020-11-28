
from game.State import Result
from typing import Any, Callable, KeysView, Optional, TypeVar
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from game.Character import Character
from game.All import All, LoadException
ALL = All("./yamlsources")

EVENTGREEN = 0xbbff45
CHARINFOBLUE = 0x2c32db
MISCORANGE = 0xff9e1f
ERRORRED = 0xe30f00
BORDERBLACK = 0x000000

class HGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game = ALL.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])
        self.resultsEmbeds: list[Embed] = []
    
    ###
    # Utility things
    ###
    
    @staticmethod
    async def getArgs(ctx: Context, args: list[str], argNames: list[str]):
        """ Remakes the arguments to be comma-separated rather than space-separated.
            Checks the number of args to make sure it matches what's expected.
            If it's not what's expected, send an error embed to the Context and return None.
            Otherwise returns the arguments. """
        
        realArgs = [s.strip() for s in " ".join(args).split(",")]
        argNamesStr = ", ".join(argNames)
        if len(realArgs) == len(argNames):
            return realArgs
        embed = Embed(
            title=f"This command needs {len(argNames)} arguments ({argNamesStr}), {len(realArgs)} recieved. Args are comma-separated.",
            color=ERRORRED
        )
        await ctx.send(embed=embed)
        return None
    
    @staticmethod
    def makeCharEmbed(char: Character, title="", description="", color=MISCORANGE):
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
    def buildEmbedFromResults(mc: Character, result: Result) -> Embed:
        """ Returns an Embed based on the Result object given by a triggered Event. """
        
        text = "\n\n".join(result.getTexts())
        embed = HGCog.makeCharEmbed(mc, "Event", text, EVENTGREEN)
        effects = result.getEffects()
        for char in effects:
            resText = "\n".join(effects[char])
            embed.add_field(name=char.string(), value=resText)
        
        return embed
    
    async def getSingleCharacter(self, ctx: Context, args: str) -> Optional[Character]:
        """ Attempts to get a loaded Character from the game based on the given args.
            If unsuccessful, sends an error embed to the given Context and returns None,
            otherwise returns the Character. """
        
        args = await HGCog.getArgs(ctx, args, ["character name"])
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
    def wrapAddCall(fun: Callable, callTitle: str, callDesc: str):
        """ Catches LoadExceptions when trying to add things to ALL. """
        try:
            fun()
        except LoadException as e:
            return Embed(
                title = callTitle,
                description = f"Encountered error:\n\n{e}",
                color = ERRORRED
            )
        return Embed(
            title = callTitle,
            description = callDesc,
            color = MISCORANGE
        )
    
    @staticmethod
    def buildListEmbed(title, sorteds: tuple[str, Any], valueFun: Callable[[Any], str], inline: bool=True):
        """ Builds an embed with a list of game objects. Used by the .list commands. """
        embed = Embed(title=title, color=MISCORANGE)
        for name, obj in sorteds:
            embed.add_field(name=name, value=valueFun(obj), inline=inline)
    
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
        
        args = await HGCog.getArgs(ctx, args, ["name", "gender/pronouns", "portrait URL"])
        if not args: return
        charName, charGender, charURL = args
        
        embed = HGCog.wrapAddCall(
            lambda: ALL.addCharacter(charName, [charGender, charURL]),
            "Add Character",
            f"Added character {charName} with gender {charGender} and image URL {charURL}"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def additem(self, ctx: Context, *args: str):
        """ Adds an Item to the game. Takes a name and a space-separated list of tags."""
        
        args = await HGCog.getArgs(ctx, args, ["name", "tags"])
        if not args: return
        itemName, itemTags = args[:2]
        
        embed = HGCog.wrapAddCall(
            lambda: ALL.addItem(itemName, itemTags),
            "Add Item",
            f"Added item {itemName} with tags {itemTags}"
        )
        await ctx.send(embed=embed)
    
    #
    # Game debugging
    #
    
    @commands.command()
    async def reload(self, ctx: Context):
        """ Reloads the game, including all added game elements. """
        
        self.game = ALL.loadGameWithSettings(["ALL"], ["ALL"], "simple", ["ALL"])
        await ctx.send("Reloaded game.")
    
    @commands.command()
    async def trigger(self, ctx: Context, *args: str):
        """ Triggers an Event. Takes the name of a loaded Character and the name of a loaded Event. """
        
        args = await HGCog.getArgs(ctx, args, ["character name", "event name"])
        if not args: return
        charName, eventName = args
        
        result = self.game.triggerByName(charName, eventName)
        char = self.game.getTributeByName(charName)
        
        embed = HGCog.buildEmbedFromResults(char, result)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def give(self, ctx: Context, *args: str):
        """ Adds an Item to a Character's inventory. Takes the name of a loaded Character and the name of a loaded Item. """
        
        args = await HGCog.getArgs(ctx, args, ["character name", "item name"])
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
        
        embed = HGCog.makeCharEmbed(char, color=CHARINFOBLUE)
        embed.add_field(name="Location:", value=char.getLocationStr())
        embed.add_field(name="Items:", value=char.getItemsStr())
        embed.add_field(name="Tags:", value=char.getTagsStr())
        embed.add_field(name="Alliance:", value=char.getAllianceStr())
        embed.add_field(name="Status:", value=char.getAliveStr())
        
        url = char.getPicture()
        if url:
            embed.set_thumbnail(url=url)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listevents(self, ctx: Context):
        """ Lists all Events currently loaded in the game. """
        
        embed = HGCog.buildListEmbed(
            "Loaded Events:",
            self.game.getSortedEvents(),
            lambda event: event.getChanceAsStr()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listitems(self, ctx: Context):
        """ Lists all Items currently loaded in the game. """
        
        embed = HGCog.buildListEmbed(
            "Loaded Items:",
            self.game.getSortedItems(),
            lambda item: item.getTagsStr()
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listzones(self, ctx: Context):
        """ Lists all Zones loaded in the game. """
        
        embed = HGCog.buildListEmbed(
            "Loaded Zones:",
            self.game.getSortedZones(),
            lambda zone: zone.getConnectionsStr(),
            False
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listchars(self, ctx: Context):
        """ Lists all Characters loaded in the game. """
        
        embed = HGCog.buildListEmbed(
            "Loaded Characters:",
            self.game.getSortedTributes(),
            lambda char: char.getAliveStr()
        )
        await ctx.send(embed=embed)
    
    #
    # Round execution
    #
    
    @commands.command()
    async def round(self, ctx: Context):
        """ Starts a game round if one is not already happening. """
        
        if self.resultsEmbeds:
            embed = Embed(
                title="There's already a round happening. Use .next to progress a round.",
                color=ERRORRED
            )
            await ctx.send(embed=embed)
            return
        
        charsAndResults = self.game.round()
        self.resultsEmbeds = []
        for char in charsAndResults:
            result = charsAndResults[char]
            self.resultsEmbeds.append(HGCog.buildEmbedFromResults(char, result))
        
        embed = Embed(
            title="Round start (use .next to progress a round)",
            color=BORDERBLACK
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def next(self, ctx: Context):
        """ Progresses a round if one is happening. """
        
        if not self.resultsEmbeds:
            embed = Embed(
                title="Round has ended, use `.round` to start another round.",
                color=ERRORRED
            )
            await ctx.send(embed=embed)
            return False
        embed = self.resultsEmbeds.pop(0)
        await ctx.send(embed=embed)
        
        if self.resultsEmbeds: return True
        
        embed = Embed(
            title="Round end (use .round to start a new round)",
            color=BORDERBLACK
        )
        await ctx.send(embed=embed)
        return False
    
    @commands.command()
    async def nextall(self, ctx: Context):
        """ Uses the `next` command until the round is over. """
        
        res = await self.next(ctx)
        while res:
            res = await self.next(ctx)
