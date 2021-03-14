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
    print(me)
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
    print(my_ranked_stats)
    tier = my_ranked_stats[0]['tier']
    rank = my_ranked_stats[0]['rank']
    LeagPoints = my_ranked_stats[0]['leaguePoints']
    await ctx.send(arg + ' is ranked ' + tier + ' ' + rank + ' (' + str(LeagPoints) + ' LP)'+ ' in Solo/Duo')



@bot.command(name='ping', help='pong')
async def test(ctx):

    await ctx.send('pong')





  


keep_alive()
bot.run(os.getenv('TOKEN'))