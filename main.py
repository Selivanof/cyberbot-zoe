import discord
import os
import requests
import json
import random
import urllib
from discord.ext import commands
from keep_alive import keep_alive
from riotwatcher import LolWatcher, ApiError
from urllib.request import urlopen
import pandas as pd

client = discord.Client()

#Setup for Riot Watcher
api_key = os.getenv('RIOT_TOKEN')
watcher = LolWatcher(api_key)

#League region
my_region = 'eun1'

#Gets the latest version of the game from DataDragon
versions_url = urlopen("https://ddragon.leagueoflegends.com/api/versions.json")
versions = json.loads(versions_url.read())
latest_version = versions[0]
#Display current league version in console
print("League of Legends version: " + latest_version)


champ_list = watcher.data_dragon.champions(latest_version, False, 'en_US')



#Bot's commands prefix
bot = commands.Bot(command_prefix='poro ')


@bot.event
async def on_ready():
  #Set custom activity
  activity = discord.Game(name="Zoe Best Champ", type=3)
  await bot.change_presence(status=discord.Status.online, activity=activity)
  #Ready
  print('Ready as {0.user}'.format(bot))


class RankedStats: 
    def __init__(self, tier, rank, LeaguePoints, fullrank, wins, losses, winrate,strwinrate): 
        self.tier = tier
        self.rank = rank
        self.LeaguePoints = LeaguePoints
        self.fullrank = fullrank
        self.wins = wins
        self.losses = losses
        self.winrate = winrate
        self.strwinrate = strwinrate

class ChampStats: 
    def __init__(self, key, name, masteryPoints, masteryLevel, wins, losses, winrate, kills, deaths, assists, kda): 
        self.key = key
        self.name = name
        self.masteryPoints = masteryPoints
        self.masteryLevel = masteryLevel
        self.wins = wins
        self.losses = losses
        self.winrate = winrate
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.kda = kda

#def getchampstats()

#Funtion that returns 
def getrankedstats(my_ranked_stats,queuetype):
  if queuetype == 2:
    tier = "N/A"
    rank = "N/A"
    LeaguePoints = 0
    fullrank = "N/A"
    wins = 0
    losses = 0
    winrate = 0
    strwinrate = "N/A"
  else:
    #Tier e.g. GOLD
    tier = my_ranked_stats[queuetype]['tier']
    #Rank e.g. IV
    rank = my_ranked_stats[queuetype]['rank']
    #LP e.g. 15
    LeaguePoints = my_ranked_stats[queuetype]['leaguePoints']
    #FullRank
    fullrank = tier+' '+rank+' ('+str(LeaguePoints)+' LP)'
    #Wins
    wins = my_ranked_stats[queuetype]['wins']
    #Losses
    losses = my_ranked_stats[queuetype]['losses']
    #Winrate
    winrate = "{:.0f}".format(100*wins/(wins+losses))
    strwinrate = str(winrate) + "%"
  return RankedStats(tier, rank, LeaguePoints, fullrank, wins, losses, winrate, strwinrate)

def returnchamp(json_object, ID, target):
    for dict,champ in json_object['data'].items():
        if str(champ['key']) == str(ID):
          #print(champ['key'])
          #print(champ[target])
          return champ[target]

@bot.command(name='stats', help='Displays player\'s level, rank, etc')
async def rank(ctx, arg):
    #Checks for errors returned from the API
    #print(versions)
    
    try:
      me = watcher.summoner.by_name(my_region, arg)
    except ApiError as err:
      if err.response.status_code == 404:
        await ctx.send('A summoner with this username does not exist in this server')
        return

    #For Debugging
    print(me)

    #Summoner Level e.g. 189
    sumlevel = me['summonerLevel']
    #Icon e.g. 1257
    icon = me['profileIconId']
    iconlink = "http://ddragon.leagueoflegends.com/cdn/" + latest_version +"/img/profileicon/" + str(icon)+".png"
    
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
    print(my_ranked_stats)
    
    #Determine if the summoner is ranked in solo/flex queues
    if len(my_ranked_stats) == 0:
      soloduo = 2
      flex = 2
    elif len(my_ranked_stats) == 1:
      if my_ranked_stats[0]['queueType'] == 'RANKED_SOLO_5x5':
        soloduo = 0
        flex = 2
      else:
        soloduo = 2
        flex = 0
    else:
      if my_ranked_stats[0]['queueType'] == 'RANKED_SOLO_5x5':
        soloduo = 0
        flex = 1
      else:
        soloduo = 1
        flex = 0
      
    #Get stats for solo/flex queues
    soloduostats = getrankedstats(my_ranked_stats,soloduo)
    flexstats = getrankedstats(my_ranked_stats,flex)
    print(soloduo)
    print(flex)
    print(soloduostats.fullrank)

    mastery_pages = watcher.champion_mastery.by_summoner(my_region, me['id'])
    topchamp = mastery_pages[0]
    print(mastery_pages)
    

    #print(returnchamp(champ_list,topchamp['championId'],'name'))


    
    #Embed Creation 
    embedVar = discord.Embed(title=arg, description='', color=0xb38531)
    embedVar.add_field(name="Level", value=str(sumlevel), inline=False)
    embedVar.add_field(name="Ranked Solo/Duo", value=soloduostats.fullrank, inline=True)
    embedVar.add_field(name="Winrate (Solo/Duo)", value=soloduostats.strwinrate, inline=True)
    embedVar.add_field(name = chr(173), value = chr(173), inline=True)
    embedVar.add_field(name="Ranked Flex", value=flexstats.fullrank, inline=True)
    embedVar.add_field(name="Winrate (Flex)", value=flexstats.strwinrate, inline=True)
    embedVar.add_field(name = chr(173), value = chr(173), inline=True)
    embedVar.add_field(name = "Top Champion", value = returnchamp(champ_list,topchamp['championId'],'name')+" ("+str(topchamp['championPoints'])+" Mastery Points)" , inline=True)
    embedVar.set_image(url=iconlink)
    #Image Link for debugging
    print(iconlink)
    
    #Send Reply
    await ctx.send(embed=embedVar)

#FREE CHAMPION ROTATION
@bot.command(name='free', help='Get the current free champion rotation')
async def free(ctx):
  #Getting champ ids from data dragon
  free_champ_rot = watcher.champion.rotations(my_region)
  champ_names = []
  #print(free_champ_rot['freeChampionIds'])
  #print(free_champ_rot['freeChampionIds'][0])
  
  #Add their names in champ_names
  for x in range(len(free_champ_rot['freeChampionIds'])):
    #print (free_champ_rot['freeChampionIds'][x])
    champ_names.append(returnchamp(champ_list,free_champ_rot['freeChampionIds'][x],'name'))
  #print(champ_names)
  
  #Creating embed
  embedVar = discord.Embed(title='Free Champion Rotation', description='Current available champions', color=0x2ea3ab)
  embedVar.add_field(name="Name", value="\n ".join(str(item) for item in champ_names), inline=True)

  #Send embed
  await ctx.send(embed=embedVar)


@bot.command(name='pop', help='pop')
async def test(ctx):

    await ctx.send('pop')





  


keep_alive()
bot.run(os.getenv('TOKEN'))