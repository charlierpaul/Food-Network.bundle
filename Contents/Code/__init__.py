BASE_URL = 'http://www.foodnetwork.com'
FULLEP_PAGE = 'http://www.foodnetwork.com/food-network-full-episodes/videos/index.html'
VID_PAGE = 'http://www.foodnetwork.com/videos.html'
TOP_VID_PAGE = 'http://www.foodnetwork.com/videos/players/food-network-top-food-videos.html'
SHOW_PAGE = 'http://www.foodnetwork.com/videos/players/food-network-full-episodes.%s.html'
SHOW_PAGE2 = 'http://www.foodnetwork.com/videos/players/food-network-top-food-videos.%s.html'
SEARCH = 'http://www.foodnetwork.com/search/search-results.videos.html?searchTerm=%s&page='
RE_XML = Regex("'vlp-player', '(.+?).videochannel")

####################################################################################################
def Start():

    ObjectContainer.title1 = 'Food Network'
    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler("/video/foodnetwork", "Food Network")
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(ShowFinder, title='Shows with Full Episodes', url=FULLEP_PAGE, source='fullep'), title='Shows with Full Episodes'))
    oc.add(DirectoryObject(key=Callback(VidHeader, title='Videos'), title='Videos'))
    oc.add(InputDirectoryObject(key=Callback(Search), title='Search for Videos', summary="Click here to search for videos", prompt="Search for the videos"))
    return oc

####################################################################################################
@route('/video/foodnetwork/showfinder')
def ShowFinder(title, url, source):

    oc = ObjectContainer(title2 = title)
    oc.add(DirectoryObject(key=Callback(ShowBrowse, url=url, title=title), title=title))
    page = HTML.ElementFromURL(url)

    for tag in page.xpath('//section[@class="video-promo"]'):
        title = tag.xpath("./header/h5")[0].text.replace(' Full Episodes','').replace(' -', '')
        channel_id = tag.xpath('.//div[@class="group"]//a/@href')[0]
        channel_id = channel_id.split('.')[1].split('.')[0]
        if source=='fullep' or 'Full Episode' in title:
            url = SHOW_PAGE %channel_id
        else:
            url = SHOW_PAGE2 %channel_id
        oc.add(DirectoryObject(key=Callback(ShowBrowse, url=url, title=title), title=title))

    return oc

####################################################################################################
@route('/video/foodnetwork/vidheader')
def VidHeader(title):

    oc = ObjectContainer(title2 = title)
    oc.add(DirectoryObject(key=Callback(ShowBrowse, url=VID_PAGE, title="Best of Food Network Videos"), title="Best of Food Network Videos"))
    oc.add(DirectoryObject(key=Callback(ShowFinder, title='Top Food Videos', url=TOP_VID_PAGE, source='clip'), title='Top Food Videos'))
    page = HTML.ElementFromURL(VID_PAGE)

    for tag in page.xpath('//section[@class="module secondary-grid section"]'):
        title = tag.xpath("./header/h5")[0].text.replace(' Full Episodes','').replace(' -', '')
        oc.add(DirectoryObject(key=Callback(VidSection,title=title), title=title))
    return oc

####################################################################################################
@route('/video/foodnetwork/vidsection')
def VidSection(title):

    oc = ObjectContainer(title2 = title)
    page = HTML.ElementFromURL(VID_PAGE)

    for tag in page.xpath('//*[text()="%s"]/parent::header/following-sibling::div//div[@class="group"]' %title):
        title = tag.xpath('.//h6//text()')[0]
        url = BASE_URL + tag.xpath('.//a/@href')[0]
        thumb = tag.xpath('.//img/@src')[0]
        oc.add(DirectoryObject(key=Callback(ShowFinder, url=url, title=title, source='clip'), title=title, thumb=thumb))

    return oc

####################################################################################################
@route('/video/foodnetwork/showbrowse')
def ShowBrowse(url, title = None):

    oc = ObjectContainer(title2=title)
    content = HTTP.Request(url).content
    xml_url = RE_XML.search(content).group(1)
    xml_url = '%s/%s.videochannel.xml' %(BASE_URL, xml_url)
    page = XML.ElementFromURL(xml_url)

    for video in page.xpath('//video'):
        title = video.xpath('./clipName')[0].text
        summary = video.xpath('./abstract')[0].text
        url = video.xpath('./permalinkUrl')[0].text
        # found a few recipes in the video lists and cannot handle videos with /sc/ in them
        # sample of sc video is http://www.foodnetwork.com/videos/sc/after-hours-hoofin-it-0216118.html
        if '/recipes/' in url or '/videos/sc/' in url:
            continue
        if not url.startswith('http://'):
            url = 'http://' + url
        duration = Datetime.MillisecondsFromString(video.xpath('./length')[0].text)
        thumb = video.xpath('./thumbnailUrl')[0].text.replace('_92x69.jpg', '_480x360.jpg')
        source = video.xpath('./sourceNetwork')[0].text

        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = summary,
            duration = duration,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc

####################################################################################################
@route('/video/foodnetwork/search', page=int)
def Search(query='', page=1):

    oc = ObjectContainer()
    local_url = SEARCH %String.Quote(query, usePlus = True) + str(page)
    html = HTML.ElementFromURL(local_url)

    for video in html.xpath('//article[@class="video"]'):
        title = video.xpath("./header/h6/a")[0].text
        summary = video.xpath("./p")[0].text
        url = BASE_URL + video.xpath("./header/h6/a/@href")[0]
        # There are a few that have /sc/ in the url and do not work with the url service
        if '/videos/sc/' in url:
            continue
        duration_list = video.xpath(".//ul/li//text()")
        duration = duration_list[len(duration_list)-1]
        duration = Datetime.MillisecondsFromString(duration.split('(')[1].split(')')[0])
        thumb = video.xpath(".//img/@src")[0].replace('_126x71.jpg', '_480x360.jpg')
        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = summary,
            duration = duration,
            thumb = Resource.ContentsOfURLWithFallback(url=thumb)
        ))

    # Paging code. 
    # There is a span code only on previos and next page so if it has an anchor it has a next page
    page_list = video.xpath('//div[@class="pagination"]/ul/li/a/span//text()')
    if page_list and 'Next' in page_list[len(page_list)-1]:
        page = page + 1
        oc.add(NextPageObject(key = Callback(Search, query=query, page=page), title = L("Next Page ...")))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos to list right now.")
    else:
        return oc
