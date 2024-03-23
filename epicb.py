import json
import discord
from discord.ext import commands
import random

# Configuration Loading
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

token = config.get('token')
prefix = config.get('prefix', '!') 

intents = discord.Intents.default()  
intents.presences = True  
intents.members = True  

bot = commands.Bot(command_prefix=prefix, intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command(name='8ball')
async def eightball(ctx):
    responses = ['Yes', 'No', 'Maybe', 'Definitely', 'Ask again later']
    await ctx.send(random.choice(responses))

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel 
    if channel is not None:
        await channel.send(f"Welcome to the server, {member.mention}!")

bot.run(token)
