import nest_asyncio
import pandas as pd
nest_asyncio.apply()

import os
from tabulate import tabulate
import copy
import discord
import json
from collections import defaultdict
from discord.ext import commands
from dotenv import load_dotenv

file = open("config.json", "r")
file = json.load(file)
TOKEN = file['token']
GUILD_TOKEN = file['guild_token']

data = pd.DataFrame(columns=['content', 'time', 'author'])

intents = discord.Intents.default()
intents.members = True

members = None
load_dotenv()
bot = commands.Bot(intents=intents, command_prefix='!')
textChannels = None
members = defaultdict(int)
@bot.event
async def on_ready():
    guild = discord.utils.find(lambda g: str(g.id) == GUILD_TOKEN, bot.guilds)
    global textChannels
    textChannels = [channel for channel in guild.channels if (channel.type == discord.ChannelType.text)]
    print(
        f'{bot.user.name} has connected to Discord!',
        f'Server: {guild.name}, Server id: {guild.id}'
    )
@bot.command(name="reset")
async def reset(ctx):
    global textChannels
    textChannels = [channel for channel in guild.channels if (channel.type == discord.ChannelType.text)]
@bot.command(name="parseserver")
async def prepMessages(ctx, arg):
    try:
        arg = int(arg)
    except:
        await ctx.send("counldn't do sorry")
        return
    message = await ctx.send('On it')
    guild = ctx.guild
    # not a dictionary
    global textChannels
    global data
    data = await parseMessages(message,textChannels,arg)
    response = f'Finished! {len(data)} messages parsed'
    await message.edit(content=response)
    
@bot.command(name="parsechannel")
async def parseChannel(ctx,arg1,arg2):
    async def getChannel(channelList):
        if(channelList is None):
            print("Invalid channelList")
            return
        
        channel = discord.utils.get(ctx.guild.channels, id=channelList[0])
        print("got channel")
        return channel
    
    if arg1 is None:
        await ctx.send("Invalid argument, two arguments expected. Received zero")
        return
    if arg2 is None:
        await ctx.send("Invalid argument, two arguments expected. Received one")
        return
    botResponse = await ctx.send(f'Beginning')
    channel = None
    try:
        channelId = int(arg1[2:-1])
        channel = discord.utils.get(ctx.guild.channels, id=channelId)
        print(channel)
        global data
        data = await parseMessages(botResponse, [channel], arg2)
        await botResponse.edit(content=f'Finished parsing {channel.name}! {len(data)} messages parsed')
    except ValueError:
        print('unable to find channel')
        return

    
    
    
        

#skips channel for sever prep
@bot.command(name="skipchannel")
async def skipChannel(ctx, *args):

  
    async def removeChannels(ctx,removeList):
        channelsRemoved = ''
        global textChannels
        for id in removeList:
            channel = discord.utils.get(ctx.guild.channels, id=id)
            textChannels.remove(channel)
            channelsRemoved += channel.name + " "
            
        await ctx.send(f'Successfully prevented  **{channelsRemoved}** from being parsed!')       

    async def printChannels():
        for channel in textChannels:
            print(channel.name, end=' ')
        print('\n')
    
    global textChannels
    removeList = await isChannelValid(ctx,args)
    await removeChannels(ctx,removeList)
    await printChannels()

    
async def isChannelValid(ctx,args):
        channelIds = [channel.id for channel in textChannels]
        i = 0
        removeList = []
        print(args)
        for arg in args:
            #If argument is a channel tag
            if(arg[:2] == '<#' and arg[-1] == '>'):
                #If the channel tag is valid
                if int(arg[2:-1]) in channelIds:
                    removeList.append(int(arg[2:-1]))
                else:
                    await ctx.send('Channel not found')
                    return
            else:
                await ctx.send('Invalid input, expected a channel tag \nTry using #nameOfChannel')
                return
        return removeList
        #await removeChannels(ctx,removeList)
    
                    
async def parseMessages(message,channels,arg):
    arg = int(arg)
    global members
    members = {}
    channelData = pd.DataFrame(columns=['channel', 'content', 'time', 'author'])
    for channel in channels:
        try:
            await message.edit(content=f'Parsing {channel.name}')# replace by editing msg
            channelMessage = await channel.history(limit=arg).flatten()
        except discord.errors.Forbidden as err:
            print(f"Skipping {channel.name}")
            continue    
        channelData = channelData.append(await createDataFrame(channelMessage))
    channelData.to_csv('messages.csv')
    return channelData
        
async def createDataFrame(messages):
    msgData = pd.DataFrame(columns=['channel','content', 'time', 'author'])
    global members
    for msg in messages:
        if msg.author.bot: continue
            
        if msg.author in members:
            members[msg.author] += 1
        else:
            members[msg.author] = 1
        msgData = msgData.append({'channel':msg.channel.name, 'content': msg.content, 'time': msg.created_at, 'author': msg.author}, ignore_index=True)
    return msgData

@bot.command(name="analmsgs")
async def analyzeMessages(ctx):
    df = pd.DataFrame(columns=['Name', "Message_Count"])
    global members
    for user in members:
        df = df.append({'Name':user.name, 'Message_Count': members[user]}, ignore_index=True)
    df = df.sort_values(by=['Message_Count'], ascending=False)
    df.to_csv('rank.csv')
    
    await ctx.send(tabulate(df[:10], showindex=False, headers=df.columns))
    
@bot.command(name="testmsgs")
async def testMessages(ctx):
    messages = pd.read_csv("messages.csv")
    members = {}
    sentMessage = await ctx.send(f'0 parsed messages')
    i = 0
    for ind,row in messages.iterrows():
        i+=1
        if i%500 == 0:
            await sentMessage.edit(content=f'{i} parsed messages')       
            
        if row['author'] in members:
            members[row['author']] += 1
        else:
            members[row['author']] = 1
    df = pd.DataFrame(columns=['Name', "Message_Count"])
    for user in members:
        df = df.append({'Name':user, 'Message_Count': members[user]}, ignore_index=True)
    df = df.sort_values(by=['Message_Count'], ascending=False)
    await ctx.send(f'Top 10 Users: \n{tabulate(df[:10], showindex=False, headers=df.columns)}')
    
    
        
        


bot.run(TOKEN)