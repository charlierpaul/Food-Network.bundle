import re, urllib
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

WEB_ROOT = 'http://www.foodnetwork.com'
VID_PAGE = 'http://www.foodnetwork.com/food-network-full-episodes/videos/index.html'
CLIPS_PAGE = 'http://www.foodnetwork.com/food-network-top-food-videos/videos/index.html'
JSON_FEED = 'http://www.foodnetwork.com/food/feeds/channel-video/0,,FOOD_CHANNEL_%s_1_50_RA,00.json'

ART =  'art-default.jpg'
ICON = 'icon-default.png'
NAME = 'Food Network'

CACHE_INTERVAL = 3600 

####################################################################################################
def Start():
  Plugin.AddPrefixHandler("/video/foodNetwork", MainMenu, NAME, ICON, ART)
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.title1 = 'Food Network'
  MediaContainer.content = 'Items'
  MediaContainer.art = R(ART)
  DirectoryItem.thumb = R(ICON)
  HTTP.SetCacheTime(CACHE_INTERVAL)

def MainMenu():
  dir= MediaContainer(viewGroup = 'List')
  dir.Append(Function(DirectoryItem(ShowFinder, title='Full Episodes'),url = VID_PAGE, title='Full Episodes'))
  dir.Append(Function(DirectoryItem(ShowFinder, title='Videos'),url = CLIPS_PAGE, title='Videos'))
  return dir
  
def ShowFinder(sender,url,title):
  dir = MediaContainer(viewGroup = 'List', title2 = title)
  page = XML.ElementFromURL(url, cacheTime=1200, isHTML=True)
  for tag in page.xpath("//ul[@class='playlists']/li"):
    title = tag.xpath("./a")[0].text.replace(' Full Episodes','')
    channel_id = tag.get("data-channel")
    dir.Append(Function(DirectoryItem(ShowBrowse, title=title), channel_id=channel_id, title=title))  
  return dir  

def GetThumb(path):
  return DataObject(HTTP.Request(path),'image/jpeg')

def ShowBrowse(sender, channel_id, title = None):
    page = XML.ElementFromURL(JSON_FEED % channel_id, cacheTime=1200, isHTML=True)

    dir = MediaContainer(viewGroup = 'Details', title2=title)
    jsonPage = HTTP.Request(JSON_FEED % channel_id)
    jsonData = JSON.ObjectFromString(jsonPage.replace('var snapTravelingLib = ',''))
    
    for vid in jsonData[0]['videos']:
		thumbpath = vid['thumbnailURL']
		title = vid['label']
		summary = vid['description']
		url = vid['videoURL']
		duration = GetDurationFromString(vid['length'])	
		dir.Append(WindowsMediaVideoItem(url, title=title,summary=summary, thumb=Function(GetThumb, path = thumbpath), duration=duration))
	
    return dir
 
def GetDurationFromString(duration):

  try:
    durationArray = duration.split(":")

    if len(durationArray) == 3:
      hours = int(durationArray[0])
      minutes = int(durationArray[1])
      seconds = int(durationArray[2])
    elif len(durationArray) == 2:
      hours = 0
      minutes = int(durationArray[0])
      seconds = int(durationArray[1])
    elif len(durationArray)  ==  1:
      hours = 0
      minutes = 0
      seconds = int(durationArray[0])
      
    return int(((hours)*3600 + (minutes*60) + seconds)*1000)
    
  except:
    return 0