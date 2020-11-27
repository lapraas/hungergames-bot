
import os

from cogs.HGCog import HGCog
from discord.ext import commands
client = commands.Bot(command_prefix=".")
    
client.add_cog(HGCog(client))

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

client.run(os.getenv("DISCORD_SECRET_THE_ANNOUNCER"))
