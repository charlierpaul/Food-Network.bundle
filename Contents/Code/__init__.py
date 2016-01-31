NAME = 'Food Network'
PREFIX = '/video/foodnetwork'
BASE_URL = 'http://www.foodnetwork.com'
FULLEP_URL = 'http://www.foodnetwork.com/videos/players/food-network-full-episodes.vc.html'
VID_PAGE = 'http://www.foodnetwork.com/videos.html'

RE_JSON = Regex('\{"channels\":.+?\}\]\}', Regex.DOTALL)
####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(FullEpMenu,  title='Full Episodes'), title='Full Episodes'))
    oc.add(DirectoryObject(key=Callback(VidFinder, title='All Videos'), title='All Videos'))
    return oc

####################################################################################################
# This function produces a list of shows from the Food Network full episodes page
@route(PREFIX + '/fullepmenu')
def FullEpMenu(title):

    oc = ObjectContainer(title2=title)

    for item in HTML.ElementFromURL(FULLEP_URL).xpath('//div[@class="pull-right"]/select/option'):

        title = item.xpath('./text()')[0]
        url = BASE_URL + item.xpath('./@value')[0]

        oc.add(DirectoryObject(
            key = Callback(ShowBrowse, url=url, title=title),
            title = title
        ))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no full episode shows to list')
    else:
        return oc

####################################################################################################
# This function produces a list of videos for a URL using the json video list in the player of each page
@route(PREFIX + '/showbrowse')
def ShowBrowse(url, title = None):

    oc = ObjectContainer(title2=title)
    content = HTTP.Request(url).content
    page = HTML.ElementFromString(content)
    
    # To prevent any issues with URLs that do not contain the video playlist json, we put the json pull in a try/except
    try:
        json_data = RE_JSON.search(content).group(0)
        #Log('the value of json_data is %s' %json_data)
        json = JSON.ObjectFromString(json_data)
    except: json = None
    #Log('the value of json is %s' %json)
    
    if json:
        for video in json['channels'][0]['videos']:
            title = video['title'].replace('&amp,', '&')
            #title = video['title']
            vid_url = video['embedUrl'].replace('.embed', '')
            # found a few recipes in the video lists
            if '/recipes/' in vid_url:
                continue
            duration = int(video['length'])*1000
            desc = video['description']
            thumb = video['thumbnailUrl'].replace('_92x69.jpg', '_480x360.jpg')

            # A couple shows include a season in the name, but they have stopped putting an episode number on shows, so there is no point in 
            # pulling videos as EpisodeObjects. We just keep the Season info in the title and if there is an episode number, it will be in the title
            oc.add(
                VideoClipObject(
                    url = vid_url,
                    title = title,
                    duration = duration,
                    summary = desc,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
                )
            )

    else:
        # If there is not a video player json, see if there is a video page navigation link on the page and send that back to this function
        try:
            video_url = BASE_URL + page.xpath('//nav/ul/li/a[@title="Videos"]/@href')[0]
            video_title = title + ' Videos'
            oc.add(DirectoryObject(key=Callback(ShowBrowse, title=video_title, url=video_url), title=video_title))
        except:
            return ObjectContainer(header=L('Empty'), message=L('This page does not contain any video'))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc

####################################################################################################
# This function produces a list of headers from the Video page
@route(PREFIX + '/vidfinder')
def VidFinder(title):

    oc = ObjectContainer(title2 = title)
    page = HTML.ElementFromURL(VID_PAGE, cacheTime = CACHE_1DAY)
    oc.add(DirectoryObject(key=Callback(TopSlide, title='Top Food Videos', url=VID_PAGE), title='Top Food Videos'))

    for tag in page.xpath('//section/header/h5/a'):
        title = tag.xpath(".//text()")[0]
        more_link = BASE_URL + tag.xpath('./@href')[0]
        # Send the Full Episode page to create a list of shows with full episodes
        if 'food-network-full-episodes' in more_link:
            oc.add(DirectoryObject(key=Callback(FullEpMenu, title=title), title=title))
        # Send the rest to pull the videos for the page with the ShowBrowse function
        else:
            oc.add(DirectoryObject(key=Callback(ShowBrowse, title=title, url=more_link), title=title))
            
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc
####################################################################################################
# This function produces a list of videos from the top slider
@route(PREFIX + '/topslide')
def TopSlide(title, url):

    oc = ObjectContainer(title2=title)

    for item in HTML.ElementFromURL(url).xpath('//div[contains(@class, "royalSlider")]/a'):
        title = item.xpath('.//h4/span/text()')[0]
        url = BASE_URL + item.xpath('./@href')[0]
        thumb = item.xpath('.//img/@src')[0]
        duration = Datetime.MillisecondsFromString(item.xpath('.//h4/cite/text()')[0].replace('(', '').replace(')', ''))

        oc.add(VideoClipObject(
            url = url,
            title = title,
            duration = duration,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no full episode shows to list')
    else:
        return oc
