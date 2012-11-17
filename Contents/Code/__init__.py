WEB_ROOT = 'http://www.foodnetwork.com'
VID_PAGE = 'http://www.foodnetwork.com/food-network-full-episodes/videos/index.html'
CLIPS_PAGE = 'http://www.foodnetwork.com/food-network-top-food-videos/videos/index.html'
JSON_FEED = 'http://www.foodnetwork.com/food/feeds/channel-video/0,,FOOD_CHANNEL_%s_1_50_RA,00.json'

ART =  'art-default.jpg'
ICON = 'icon-default.png'

####################################################################################################
def Start():
    ObjectContainer.title1 = 'Food Network'
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)

@handler("/video/foodNetwork", "Food Network", thumb=ICON, art=ART)
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(ShowFinder, url=VID_PAGE, title='Full Episodes'), title='Full Episodes'))
    oc.add(DirectoryObject(key=Callback(ShowFinder, url=CLIPS_PAGE, title='Videos'), title='Videos'))
    return oc

@route('/video/foodNetwork/showfinder')
def ShowFinder(url,title):
    oc = ObjectContainer(title2 = title)
    page = HTML.ElementFromURL(url)
    for tag in page.xpath("//ul[@class='playlists']/li"):
        title = tag.xpath("./a")[0].text.replace(' Full Episodes','').replace(' -', '')
        channel_id = tag.get("data-channel")
        oc.add(DirectoryObject(key=Callback(ShowBrowse, channel_id=channel_id, title=title), title=title))
    oc.objects.sort(key = lambda obj: obj.title)
    return oc

@route('/video/foodNetwork/showbrowse')
def ShowBrowse(channel_id, title = None):
    page = HTML.ElementFromURL(JSON_FEED % channel_id)

    oc = ObjectContainer(title2=title)
    jsonPage = HTTP.Request(JSON_FEED % channel_id).content
    jsonData = JSON.ObjectFromString(jsonPage.replace('var snapTravelingLib = ',''))
    
    for vid in jsonData[0]['videos']:
        thumbpath = vid['thumbnailURL']
        title = vid['label']
        summary = vid['description']
        url = vid['videoURL'].replace('http://wms','rtmp://flash')
        if url.find('ondemand') == -1:
            url = url.replace('scrippsnetworks.com','scrippsnetworks.com/ondemand')
        url = url.replace('ondemand/','ondemand/&')
        url = url.replace('.wmv','')
        url = url.split('&')
        duration = Datetime.MillisecondsFromString(vid['length'])
        oc.add(VideoClipObject(
            key=Callback(VideoDetail, title=title, summary=summary, thumb=thumbpath, duration=duration, rtmp_url=url[0], clip=url[1]),
            rating_key=url[0]+'&'+url[1],
            title=title,
            summary=summary,
            duration=duration,
            thumb=Resource.ContentsOfURLWithFallback(url=[thumbpath.replace('92x69', '480x360'), thumbpath], fallback=ICON),
            items=[
                MediaObject(
                    parts=[PartObject(key=RTMPVideoURL(url=url[0], clip=url[1]))]
                    )
                ]
            )     
        )
    return oc

@route('/video/foodNetwork/videodetail')
def VideoDetail(title, summary, thumb, duration, rtmp_url, clip):
    oc = ObjectContainer()
    oc.add(VideoClipObject(
        key=Callback(VideoDetail, title=title, summary=summary, thumb=thumb, duration=duration, rtmp_url=url[0], clip=url[1]),
        rating_key=url[0]+'&'+url[1],
        title=title,
        summary=summary,
        duration=duration,
        thumb=Resource.ContentsOfURLWithFallback(url=[thumb.replace('92x69', '480x360'), thumb], fallback=ICON),
        items=[
            MediaObject(
                parts=[PartObject(key=RTMPVideoURL(url=rtmp_url, clip=clip))]
                )
            ]
        )
    )
    return oc