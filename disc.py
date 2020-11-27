
import os

from discord.ext.commands.context import Context

from HGCog import HGCog
from discord.ext import commands
client = commands.Bot(command_prefix=".")
    
client.add_cog(HGCog(client))

@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")

@client.check
def printCommand(ctx: Context):
    print(f"{ctx.message.author.name}: {ctx.message.content}")
    return True

client.run(os.getenv("DISCORD_SECRET_THE_ANNOUNCER"))
