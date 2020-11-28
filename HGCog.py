
from game.State import Result
from typing import Callable, Optional
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from game.Character import Character
from game.All import All
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
    
    @staticmethod
    async def getArgs(ctx: Context, args: list[str], argNames: list[str]):
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
        embed = Embed(title=char.string() if not title else title, description=description, color=color)
        url = char.getPicture()
        if url:
            embed.set_thumbnail(url=url)
        return embed
    
    def buildEmbedFromResults(self, mc: Character, result: Result) -> Embed:
        text = "\n\n".join(result.getTexts())
        embed = HGCog.makeCharEmbed(mc, "Event", text, EVENTGREEN)
        effects = result.getEffects()
        for char in effects:
            resText = "\n".join(effects[char])
            embed.add_field(name=char.string(), value=resText)
        
        return embed
    
    async def getSingleCharacter(self, ctx: Context, args: str) -> Optional[Character]:
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
        return char
    
    @commands.command()
    async def ping(self, ctx: Context):
        """ Responds with "Pong!" """
        await ctx.send("Pong!")
    
    @commands.command()
    async def addchar(self, ctx: Context, *args: str):
        """ Adds a Character to the game. Takes a name, a gender or space-separated list of pronouns, and a portrait URL. """
        
        args = await HGCog.getArgs(ctx, args, ["name", "gender/pronouns", "portrait URL"])
        if not args: return
        charName, charGender, charURL = args
        
        res = ALL.addCharacter(charName, [charGender, charURL])
        if res:
            embed = Embed(
                title="Add Character",
                description="Encountered error:\n\n" + res,
                color=ERRORRED
            )
            await ctx.send(embed=embed)
            return
        
        embed = Embed(
            title="Add Character",
            description=f"Added character {charName} with gender {charGender} and image URL {charURL}",
            color=MISCORANGE
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def additem(self, ctx: Context, *args: str):
        """ Adds an Item to the game. Takes a name and a space-separated list of tags."""
        
        args = await HGCog.getArgs(ctx, args, ["name", "tags"])
        if not args: return
        itemName, itemTags = args[:2]
        
        res = ALL.addItem(itemName, itemTags)
        if res:
            embed = Embed(
                title="Add Item",
                description="Encountered error:\n\n" + res,
                color=ERRORRED
            )
            await ctx.send(embed=embed)
            return
        
        embed = Embed(
            title="Add Item",
            description=f"Added item {itemName} with tags {itemTags}",
            color=MISCORANGE
        )
        await ctx.send(embed=embed)
    
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
        
        embed = self.buildEmbedFromResults(char, result)
        await ctx.send(embed=embed)
    
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
            self.resultsEmbeds.append(self.buildEmbedFromResults(char, result))
        
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
        
        embed = Embed(
            title = "All events:",
            color = MISCORANGE
        )
        for event in self.game.events:
            embed.add_field(name=event.name, value=event.chance)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listitems(self, ctx: Context):
        """ Lists all Items currently loaded in the game. """
        
        embed = Embed(
            title = "All items:",
            color = MISCORANGE
        )
        for item in self.game.items:
            embed.add_field(name=item.string(), value=item.getTagsStr())
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listcommands(self, ctx: Context):
        """ Lists all commands. """
        
        embed = Embed(
            title = "All commands:",
            color = MISCORANGE
        )
        for command in ctx.bot.commands:
            embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listzones(self, ctx: Context):
        """ Lists all Zones loaded in the game. """
        
        embed = Embed(
            title = "Map:",
            color = MISCORANGE
        )
        for zone in self.game.map.zones:
            embed.add_field(name=zone.name, value=zone.getConnxStr(), inline=False)
        await ctx.send(embed=embed)
    
    @commands.command()
    async def listchars(self, ctx: Context):
        """ Lists all Characters loaded in the game. """
        
        embed = Embed(
            title = "Characters:",
            color = MISCORANGE
        )
        for character in self.game.tributes:
            embed.add_field(name=character.string(), value=character.getLocationStr())
        await ctx.send(embed=embed)
