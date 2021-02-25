import os
import json
import discord
from dotenv import load_dotenv

file = open("config.json", "r")
TOKEN = json.load(file)
TOKEN = TOKEN['token']

load_dotenv()
client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

client.run(TOKEN)
