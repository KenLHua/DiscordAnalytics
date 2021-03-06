## ~ WIP ~
# What does DiscordAnalytics do?
* Parse messages in all channels (that the bot has permission to see) in a discord server 
   * Remove channels from the parsing list using their channel id
* Parse messages in a single channel
* Presents that data in a stacked bar plot

Steps to begin: 

0. Setup a discord bot within the discord dev console and invite it to your desired server w/ relevant permissions
1. Create a config.json file in /input/, with fields:
   {"token" : BOT_TOKEN_STRING, "guild_token": GUILD_TOKEN_STRING}
2. Create a blacklist.json file in /input/, with fields:
   {"filterList": [CHANNEL_ID_TO_BLACKLIST1,CHANNEL_ID_TO_BLACKLIST2]}
3. Type "!parseserver #MESSAGE_COUNT", with #MESSAGE_COUNT being how many messages to parse in each channel
4. Type "!analyzemsgs", below is an example of the output, but with anonymized names and channels
   
Example of output:

![alt text](https://github.com/KenLHua/DiscordAnalytics/blob/master/saved_figure.png?raw=true))


## Todo:
[] - Label graph output

[] - Choice of channel on x-axis

[] - User's favorite words

[] - Words most often used in the server/channel

[] - Unit tests/CI with pushes
