import discord
import os
import requests
import json
import random
from discord.ext import commands
from keep_alive import keep_alive
from riotwatcher import LolWatcher, ApiError
import pandas as pd

client = discord.Client()

api_key = os.getenv('RIOT_TOKEN')
watcher = LolWatcher(api_key)

my_region = 'eun1'


bot = commands.Bot(command_prefix='pog ')


@bot.event
async def on_ready():
  print('Logged in as {0.user}'.format(bot))


@bot.command(name='stats', help='Displays player\'s level, rank, etc')
async def rank(ctx, arg):
    me = watcher.summoner.by_name(my_region, arg)
    #For Debugging
    print(me)
    
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
    print(my_ranked_stats)

    soloduo = 0
    flex = 1
    if my_ranked_stats[0]['queueType'] == 'RANKED_SOLO_5x5':
      soloduo = 0
      flex = 1
    else:
      soloduo = 1
      flex=0
   #Tier e.g. GOLD
    tier = my_ranked_stats[soloduo]['tier']
    #Rank e.g. IV
    rank = my_ranked_stats[soloduo]['rank']
    #LP e.g. 15
    LeaguePoints = my_ranked_stats[soloduo]['leaguePoints']
    #FullRank
    fullrank = tier+' '+rank+' ('+str(LeaguePoints)+' LP )'
    #Summoner Level e.g. 189
    sumlevel = me['summonerLevel']
    #Wins
    wins = my_ranked_stats[soloduo]['wins']
    #Losses
    losses = my_ranked_stats[soloduo]['losses']
    #Winrate
    winrate = "{:.2f}".format(wins/(wins+losses))
    #Inactive e.g. True
    inactive = my_ranked_stats[soloduo]['inactive']
    #HotStreak e.g. False
    hotStreak = my_ranked_stats[soloduo]['hotStreak']
    #Icon e.g. 1257
    icon = me['profileIconId']
    iconlink = "http://ddragon.leagueoflegends.com/cdn/10.18.1/img/profileicon/" + str(icon)+".png"
    #Extra for hot streaks etc
    extra = ''
    if hotStreak: 
      extra = '*This player is on a hot streak!*'

    #Embed Creation 
    embedVar = discord.Embed(title=arg, description='', color=0xb38531)
    embedVar.add_field(name="Level", value=str(sumlevel), inline=True)
    embedVar.add_field(name="Ranked Solo/Duo", value=fullrank, inline=True)
    embedVar.add_field(name="Winrate (Solo/Duo)", value=str(winrate) +'%', inline=False)
    embedVar.set_image(url=iconlink)
    #Image Link for debugging
    print(iconlink)
    
    #Send Reply
    await ctx.send(embed=embedVar)



@bot.command(name='ping', help='pong')
async def test(ctx):

    await ctx.send('pong')





  


keep_alive()
bot.run(os.getenv('TOKEN'))