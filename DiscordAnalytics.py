import os
import sys
import pandas as pd
import copy
import discord
import json
from collections import defaultdict
from discord.ext import commands
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import re
import nltk
from nltk.corpus import stopwords

# Loading bot credentials
file = open("input/config.json", "r")
file = json.load(file)
TOKEN = file['token']
GUILD_TOKEN = file['guild_token']

# Initializing variables
stopwords = set(stopwords.words('english')) 
data = pd.DataFrame(columns=['content', 'time', 'author'])
members = None
textChannels = None

# Startup flags
minWordLength = 2 # Include only words that are >= character length
preloadBlacklist = True # Exclude channels from a blacklist file
printTotal = False # Include number of messages in the output
userMsgThreshold = 0 # Only include users that have >= messages
channelMsgThreshold= 0 # Only include channels that have >= messages
#
intents = discord.Intents.default()
intents.members = True


load_dotenv()
bot = commands.Bot(intents=intents, command_prefix='!')

if(preloadBlacklist):
    blacklist = open("input/blacklist.json","r")
    blacklist = json.load(blacklist)
    blacklist = blacklist['filterList']

members = defaultdict(int)
@bot.event
async def on_ready():
    guild = discord.utils.find(lambda g: str(g.id) == GUILD_TOKEN, bot.guilds)
    global textChannels
    textChannels = [channel for channel in guild.channels if (channel.type == discord.ChannelType.text) and 
                   str(channel.id) not in blacklist]
    print(
        f'{bot.user.name} has connected to Discord!',
        f'Server: {guild.name}, Server id: {guild.id}'
    )
    
''' Reinitializes parseable channels to be all channels inside the Discord server
    Parameters:
        ctx - context
    Returns: None
'''
@bot.command(name="reset")
async def reset(ctx):
    global textChannels
    textChannels = [channel for channel in ctx.guild.channels if (channel.type == discord.ChannelType.text)]
    await ctx.send("Reset channel parse list to include all channels.")
    
''' Parses the server using channels inside textChannels
    Paramters:
        ctx - context
        arg - number of messages to parse in each channel
    Return: None
'''
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
    
''' Parses only the channel provided
    Parameters: 
        ctx - context
        arg1 - channel id
        arg2 - number of messages to parse
    Return: None
'''
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
        global textChannels
        textChannels = [channel]
        global data
        data = await parseMessages(botResponse, [channel], arg2)
        await botResponse.edit(content=f'Finished parsing {channel.name}! {len(data)} messages parsed')
    except ValueError:
        print('unable to find channel')
        return

    
    
    
        


''' Removes channel(s) from parseable channels when using parseserver command
    Paramters: 
        ctx - context
        *args - list of channel ids to remove
    Return: None
'''
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

''' Verifies if channel exists in parseable channels
    Parameters:
        ctx - context
        args - list of channel ids to remove
    Returns: List, list of parseable channels
'''
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
    
''' Obtains messages from channels,returns dataframe with those messages
    Parameters:
        message - context message, keeps the user informed on what channel is being parsed
        channels - whitelist of channels to parse
        arg - number of messages to parse within each channel
    Returns : DataFrame
'''
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
            global textChannels
            textChannels.remove(channel)
            print(f"Skipping {channel.name}")
            continue    
        channelData = channelData.append(await createDataFrame(channelMessage))
    channelData.to_csv("output/messages.csv")
    return channelData

''' Expects iterable object channelMessages
    Parameters:
        messages - iterable messages from Discord API
    Returns : DataFrame
'''
async def createDataFrame(messages):
    msgData = pd.DataFrame(columns=['channel','content', 'time', 'author'])
    
    # members = {user: [{channel: message_count}, user_message_count]}
    global members
    
    global textChannels
    channels = textChannels
    for msg in messages:
        if msg.author.bot: continue
        message = [word for word in str(msg.content).split() 
                   if word not in stopwords and len(word) < minWordLength]
        if len(message) == 0 :continue
        user = msg.author
        channel = msg.channel
        message = str(msg.content).split()
                   
        if user in members:
            members[user][0][channel] += len(message)
            members[user][0]['!total'] += len(message)
            members[user][1] += len(message)
        else:
            members[user] = [{channel: 0 for channel in channels}, 0]
            members[user][0][channel] = len(message)
            members[user][0]['!total'] = len(message)
            members[user][1] = len(message)
        try:
            msgData = msgData.append({'channel':msg.channel.name, 'content': msg.content, 'time': msg.created_at, 'author': msg.author}, ignore_index=True)
            
        except ValueError:
            print('error')
    return msgData

''' Saves and messages plot/visualization of messages in output/saved_figure.png
    Parameter: ctx - context
    Return: None
'''
@bot.command(name="analyzemsgs")
async def analyzeMessages(ctx):
    
    global printTotal
    global userMsgThreshold
    global channelMsgThreshold
    global textChannels
    print(textChannels)
    channels = textChannels
    channelToUser = {remove_emoji(channel.name): {} for channel in channels}
    channelToUser['!Total'] = {}
    
    for user in members:
        if members[user][1] >= userMsgThreshold:
            for channel in members[user][0]:
                if channel != '!total' and channel in textChannels:
                    channelName = remove_emoji(channel.name)
                    # use channelName for channelToUser since it'll print out prettier
                    # use channel for member since it refers to object channel, not name
                    channelToUser[channelName][user] = members[user][0][channel]
            channelToUser['!Total'][user] = members[user][1]
    data = pd.DataFrame(channelToUser)
    # create a uhhhhhhh boolean for x-axis channels, y-axis user msgs
    
    
    
    # create a boolean for x-axis users, y-axis channels
    data.loc['Total'] = data.sum()
    data = data.sort_values(by='Total', ascending=False, axis=1)
    data = data.sort_values(by='!Total', ascending=False)
    if not printTotal:
        data=data.drop('Total',axis=0)
    data = data.drop(columns=['!Total'])
    data.plot(kind="bar",stacked=True, figsize=(15,15),colormap='tab20')
    plt.savefig('output/saved_figure.png')
    await ctx.send(file=discord.File('output/saved_figure.png'))
    
    
@bot.command(name="testmsgs")
async def testMessages(ctx):
    messages = pd.read_csv(os.path.join(script_dir, '../output/messages.csv'))
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
    #await ctx.send(f'Top 10 Users: \n{tabulate(df[:10], showindex=False, headers=df.columns)}')
    
    
    
    
def remove_emoji(string):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)
    

        
        


bot.run(TOKEN)