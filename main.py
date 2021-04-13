# install +https://.com/meraki-analytics/-.git
#pip install colorthief
import discord
import os
import requests
import json
import random
import urllib
from discord.ext import commands
from keep_alive import keep_alive
from riotwatcher import LolWatcher, ApiError
from urllib.request import urlopen, Request
from roleidentification import pull_data, get_roles
import pandas as pd
from colorthief import ColorThief
import io

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

print("\nLoading queue data...")
queuetypes = json.loads(urlopen("http://static.developer.riotgames.com/docs/lol/queues.json").read())
print("Queue data loaded")

print("\nLoading roles data...")
champion_roles = pull_data()
print("Roles data loaded")



print("\nLoading champion data...")
champ_list = watcher.data_dragon.champions(latest_version, False, 'en_US')
print("Champion data loaded")



#Bot's commands prefix
bot = commands.Bot(command_prefix='poro ')


@bot.event
async def on_ready():
  #Set custom activity
  activity = discord.Game(name="Zoe Best Champ", type=3)
  await bot.change_presence(status=discord.Status.online, activity=activity)
  #Ready
  print('Bot ready ( {0.user} )'.format(bot))


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
    def __init__(self, key, name, masteryPoints, masteryLevel, masteryTokens, wins, losses, winrate, kills, deaths, assists, kda, totalmatches, samplematches): 
        self.key = key
        self.name = name
        self.masteryPoints = masteryPoints
        self.masteryLevel = masteryLevel
        self.masteryTokens = masteryTokens
        self.wins = wins
        self.losses = losses
        self.winrate = winrate
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.kda = kda
        self.totalmatches = totalmatches
        self.samplematches = samplematches

class team: 
    def __init__(self): 
        self.names = []
        self.champs = []
        self.champkeys = []
        self.ranks = []



#def getchampstats()

#Funtion that returns 
def getrankedstats(my_ranked_stats,queuetype):
  if queuetype == 2:
    tier = "N/A"
    rank = "N/A"
    LeaguePoints = 0
    fullrank = "Unranked"
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

#Returns champion data based on their key
def returnchamp(json_object, ID, target):
    for dict,champ in json_object['data'].items():
        if str(champ['key']) == str(ID):
          #print(champ['key'])
          #print(champ[target])
          return champ[target]

def getchampid(json_object, name):
    for dict,champ in json_object['data'].items():
        if str(champ['name']) == name:
          #print(champ['key'])
          #print(champ[target])
          return champ['key']


#Gets info from the Summoner API
def getsuminfo(ctx, arg):
  channel = bot.get_channel(ctx.channel.id)
  try:
      me = watcher.summoner.by_name(my_region, arg)
  except ApiError as err:
      if err.response.status_code == 404:
        bot.loop.create_task(channel.send('A summoner with this username does not exist in this server'))
        return 0
      elif err.response.status_code == 403:
        bot.loop.create_task(channel.send('Please contact the bot\'s developer: Error 403'))
        return 0
  return me

#0 is soloduo 1 is flex
def getqueuenums(my_ranked_stats, queue):
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
    if queue == 0: 
      return soloduo
    else: 
      return flex

#stat==0 KDA -- stat==1 Winrate
def getchampstats(ctx, sumID, champ):
  me = getsuminfo(ctx,sumID)

  name = champ.title()

  champ_id=getchampid(champ_list,name)

  match_details=[]
  mastery_pages = watcher.champion_mastery.by_summoner(my_region, me['id'])
  masterylevel=0
  masterypoints=0
  masteryTokens=0
  kills = 0
  deaths = 0
  assists = 0
  wins = 0
  samplegames = 10
  #Get match info
  try:
      match_history = watcher.match.matchlist_by_account(my_region, me['accountId'],champion = champ_id)
  except ApiError as err:
      if err.response.status_code == 404:
        print("No games found")
        return ChampStats(champ_id,name,0,0,0,"N/A","N/A", "N/A", "N/A","N/A","N/A","N/A",0,0)
      elif err.response.status_code == 403:
        print("Error 403")
        return ChampStats(champ_id,name,0,0,0,"N/A","N/A", "N/A", "N/A","N/A","N/A","N/A",0,0)
  
  num_games=len(match_history["matches"])
  #print(match_history)
  
  for x in range(samplegames):
    #print (num_games)
    if x >= num_games:
      samplegames = num_games
      break
    match_details.append(watcher.match.by_id(my_region, match_history["matches"][x]["gameId"]))
    for y in range(10):
      if match_details[x]["participantIdentities"][y]["player"]["accountId"] == me['accountId']:
        participant = y
        break;
    kills = kills + match_details[x]["participants"][participant]["stats"]["kills"]
    deaths = deaths + match_details[x]["participants"][participant]["stats"]["deaths"]
    assists = assists + match_details[x]["participants"][participant]["stats"]["assists"]
    if match_details[x]["participants"][participant]["stats"]["win"] == True:
      wins = wins +1 
  

  if deaths != 0:
    kda = "{:.2f}".format((kills+assists)/deaths)
  else:
    kda = "Perfect"

  winrate ="{:.0f}".format(wins/samplegames*100)
  for z in range(len(mastery_pages)):
    if str(mastery_pages[z]["championId"]) == str(champ_id):
      masterylevel = mastery_pages[z]["championLevel"]
      masterypoints = mastery_pages[z]["championPoints"]
      masteryTokens = mastery_pages[z]["tokensEarned"]

  return ChampStats(champ_id,name,masterypoints,masterylevel,masteryTokens,wins,match_history["totalGames"] - wins, winrate, kills,deaths,assists,kda,match_history["totalGames"],samplegames)




#COMMANDS


@bot.command(name='stats', help='Get player stats')
async def rank(ctx, arg):
    #Checks for errors returned from the API
    #print(versions)
    print("Command received: stats")
    me = getsuminfo(ctx,arg)
    if me == 0:
      return
    

    #For Debugging
    #print(me)

    #Summoner Level e.g. 189
    sumlevel = me['summonerLevel']
    #Icon e.g. 1257
    icon = me['profileIconId']
    iconlink = "http://ddragon.leagueoflegends.com/cdn/" + latest_version +"/img/profileicon/" + str(icon)+".png"
    
    my_ranked_stats = watcher.league.by_summoner(my_region, me['id'])
    #print(my_ranked_stats)
      
    #Get stats for solo/flex queues
    soloduostats = getrankedstats(my_ranked_stats,getqueuenums(my_ranked_stats,0))
    flexstats = getrankedstats(my_ranked_stats,getqueuenums(my_ranked_stats,1))

    #print(soloduostats.fullrank)

    mastery_pages = watcher.champion_mastery.by_summoner(my_region, me['id'])
    topchamp = mastery_pages[0]
    #print(mastery_pages)
    

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
    #print(iconlink)
    
    #Send Reply
    await ctx.send(embed=embedVar)
    print("Command completed: stats")

#FREE CHAMPION ROTATION
@bot.command(name='free', help='Get the current free champion rotation')
async def free(ctx):
  print("Command received: free")
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
  print("Command completed: game")

#GET CURRENT GAME INFO
@bot.command(name='game', help='Get current game info for a summoner')
async def game(ctx, arg, sum='None'):
  print("Command received: game")
  #Get summoner info
  me = getsuminfo(ctx,arg)
  
  #Get match info
  try:
      specinfo = watcher.spectator.by_summoner(my_region, me["id"])
  except ApiError as err:
      if err.response.status_code == 404:
        await ctx.send('This summoner is not currently in a game')
        return
      elif err.response.status_code == 403:
        await ctx.send('Please contact the bot\'s developer: Error 403')
        return
  
  #print(specinfo)
  blue=team()
  red=team()
  gametime = str(int((specinfo["gameLength"]+180)/60)) +":" + str(int(specinfo["gameLength"])%60)
  
  for x in range(len(queuetypes)):
    if str(queuetypes[x]["queueId"]) == str(specinfo["gameQueueConfigId"]):
      game_mode = queuetypes[x]["description"]

  game_mode = game_mode.rsplit(' ', 1)[0]
  #print(game_mode)

  if specinfo["gameQueueConfigId"] == 440:
    mode = 1
  else:
    mode = 0
  
 #Getting keys
  bluekeys = []
  redkeys = []

  for x in range(len(specinfo["participants"])):
    if specinfo["participants"][x]["teamId"] == 100:
      bluekeys.append(specinfo["participants"][x]['championId'])
      
      if specinfo["participants"][x]['spell1Id'] == 11 or specinfo["participants"][x]['spell2Id'] == 11:
        bluejungler = specinfo["participants"][x]['championId']
    else:
      redkeys.append(specinfo["participants"][x]['championId'])
      
      if specinfo["participants"][x]['spell1Id'] == 11 or specinfo["participants"][x]['spell2Id'] == 11:
        redjungler = specinfo["participants"][x]['championId']

#Getting roles
  blueroles=get_roles(champion_roles,bluekeys,jungle=bluejungler)
  redroles=get_roles(champion_roles,redkeys,jungle=redjungler)
  blueindex = []
  redindex = []
  for role,key in blueroles.items():
    for x in range(len(bluekeys)):
      if key == bluekeys[x]:
        blueindex.append(x)
        
  for role,key in redroles.items():
    for x in range(len(redkeys)):
      if key == redkeys[x]:
        redindex.append(x)
  
  #Getting info
  for x in range(len(specinfo["participants"])):
    if specinfo["participants"][x]["teamId"] == 100:
      blue.names.append(specinfo["participants"][blueindex[x]]['summonerName'])
      blue.champs.append(returnchamp(champ_list,specinfo["participants"][blueindex[x]]['championId'],'name'))
      my_ranked_stats = watcher.league.by_summoner(my_region, specinfo["participants"][blueindex[x]]['summonerId'])
      mode = 0
      blue.ranks.append(getrankedstats(my_ranked_stats,getqueuenums(my_ranked_stats,mode)).fullrank)
    else:
      red.names.append(specinfo["participants"][redindex[x-5]+5]['summonerName'])
      red.champs.append(returnchamp(champ_list,specinfo["participants"][redindex[x-5]+5]['championId'],'name'))
      my_ranked_stats = watcher.league.by_summoner(my_region, specinfo["participants"][redindex[x-5]+5]['summonerId'])
      mode = 0
      red.ranks.append(getrankedstats(my_ranked_stats,getqueuenums(my_ranked_stats,mode)).fullrank)

  #print(blueroles)


 
  #print (blue.ranks)
  #print(red)
  GeneralEmbed = discord.Embed(title="**"+ game_mode +"**  ", description="Match Time: " + gametime, color=0xb38531)
  
  
  #BLUE TEAM
  BlueEmbed = discord.Embed(title="Blue Team", description=" ", color=0x3266a8)
  BlueEmbed.add_field(name="  Summoner", value="\n ".join(str(item) for item in blue.names), inline=True)
  BlueEmbed.add_field(name="Champion", value="\n ".join(str(item) for item in blue.champs), inline=True)
  BlueEmbed.add_field(name="Rank", value="\n ".join(str(item) for item in blue.ranks), inline=True)
  
  #RED TEAM
  RedEmbed = discord.Embed(title="Red Team", description=" ", color=0xb82121)
  RedEmbed.add_field(name="  Summoner", value="\n ".join(str(item) for item in red.names), inline=True)
  RedEmbed.add_field(name="Champion", value="\n ".join(str(item) for item in red.champs), inline=True)
  RedEmbed.add_field(name="Rank", value="\n ".join(str(item) for item in red.ranks), inline=True)
  await ctx.send(embed=GeneralEmbed)
  await ctx.send(embed=BlueEmbed)
  await ctx.send(embed=RedEmbed)
  print("Command completed: game")
  
@bot.command(name='champ', help='get summoner\'s stats for a specific champion')
async def champ(ctx,arg1,arg2):
  print("Command received: champ")
  
  champion = getchampstats(ctx,arg1,arg2)

  iconlink="http://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/" + str(champion.key) + ".png"
  
  #Icon Main Colors
  print("Starting")
  req = Request(iconlink, headers={'User-Agent': 'Mozilla/5.0'})
  icon = urlopen(req)
  color_thief = ColorThief(icon)
  main_color = color_thief.get_color(quality=6)
  print(main_color)
  hex_str = "0x" + ("%02X%02X%02X" % main_color)
  main_color_hex = int(hex_str, 16) + 0x200


  #Champion Mastery Text Creation
  if champion.masteryLevel != 7:
    if champion.masteryTokens == 1:
      masterytext=str(champion.masteryPoints) + " ( Level "+str(champion.masteryLevel)+" - Has "+ str(champion.masteryTokens) + " token for Level " + str(champion.masteryLevel + 1) + " )"
    else:
      masterytext=str(champion.masteryPoints) + " ( Level "+str(champion.masteryLevel)+" - Has "+ str(champion.masteryTokens) + " tokens for Level " + str(champion.masteryLevel + 1) + " )"
  else:
    masterytext=str(champion.masteryPoints) + " ( Level "+str(champion.masteryLevel)+" )"
  
  
  #Embed Creation 
  embedVar = discord.Embed(title=arg1 + " - " + arg2, description='', color=main_color_hex)
  embedVar.add_field(name="Games Played", value=champion.totalmatches, inline=True)
  embedVar.add_field(name="Winrate", value=str(champion.winrate) + "%", inline=True)
  embedVar.add_field(name="Champion Mastery", value=masterytext, inline=False)
  
  embedVar.set_image(url=iconlink)
  #Image Link for debugging
  #print(iconlink)
  
  #Send Reply
  await ctx.send(embed=embedVar)
  print("Command completed: stats")

  


#FOR TESTING PURPOSES
@bot.command(name='pop', help='pop')
async def test(ctx):
  
  await ctx.send('pop')





  


keep_alive()
bot.run(os.getenv('TOKEN'))