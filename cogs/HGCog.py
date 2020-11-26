
from discord.embeds import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from Character import Character, yamlCharacter
from loads import add, defaultLoad

class HGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game = defaultLoad()
    
    @staticmethod
    async def getArgs(ct: int, ctx: Context, args: list[str]):
        realArgs = [s.strip() for s in " ".join(args).split(",")]
        if len(realArgs) == ct:
            return realArgs
        await ctx.send(f"This command needs {ct} arguments, {len(realArgs)} recieved (args are comma-separated)")
        return None
    
    def buildEmbed(self, mcName: str, resTexts: list[tuple[str, list[tuple[Character, str]]]]) -> list[Embed]:
        mc = self.game.getTributeByName(mcName)
        if not mc: return [Embed(title="Error", description=f"Main character {mcName} not found")]
        
        embeds = []
        for eventText, ress in resTexts:
            embed = Embed(description=eventText)
            url = mc.getPicture()
            if url:
                embed.set_thumbnail(url=mc.getPicture())
            for char, resText in ress:
                embed.add_field(name=char.string(), value=resText)
            embeds.append(embed)
        return embeds
    
    @commands.command()
    async def ping(self, ctx: Context):
        await ctx.send("Pong!")
    
    @commands.command()
    async def reload(self, ctx: Context):
        self.game = defaultLoad()
        await ctx.send("Reloaded game.")
    
    @commands.command()
    async def trigger(self, ctx: Context, *args: str):
        args = await HGCog.getArgs(2, ctx, args)
        if not args: return
        charName, eventName = args
        resTexts = self.game.triggerByName(charName, eventName)
        embeds = self.buildEmbed(charName, resTexts)
        for embed in embeds:
            await ctx.send(embed=embed)
    
    @commands.command()
    async def give(self, ctx: Context, *args: str):
        args = await HGCog.getArgs(2, ctx, args)
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
    async def addCharacter(self, ctx: Context, *args: str):
        args = await HGCog.getArgs(3, ctx, args)
        if not args: return
        charName, charGender, charURL = args
        add("./yamlsources/characters/adds.yaml", yamlCharacter, [charName, charGender, charURL])
        await ctx.send(f"Added character {charName} with gender {charGender} and image URL {charURL}")
    
    @commands.command()
    async def addItem(self, ctx: Context, *args: str):
        args = await HGCog.getArgs(2, ctx, args)
        if not args: return
        itemName, itemTags = args
        itemTags = itemTags.split(" ")
