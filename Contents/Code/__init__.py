TITLE = 'Old Movie Time'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"
BASE_URL = "http://oldmovietime.com/"
PREFIX = '/video/oldmovietime'

EPISODES_PER_PAGE = 12

PREDEFINED_CATEGORIES = [ 
    {
        'title':    'Now Showing',
        'url':      BASE_URL
    },
    {
        'title':    'Action/Adventure',
        'url':      BASE_URL + 'action_adventure.html'
    },
    {
        'title':    'Family',
        'url':      BASE_URL + 'family.html'
    },
    {
        'title':    'Comedy',
        'url':      BASE_URL + 'comedy.html'
    },
    {
        'title':    'War',
        'url':      BASE_URL + 'war.html'
    },
    {
        'title':    'Westerns',
        'url':      BASE_URL + 'westerns.html'
    },
    {
        'title':    'Drama',
        'url':      BASE_URL + 'drama.html'
    },
    {
        'title':    'Crime/Mystery',
        'url':      BASE_URL + 'crime_mystery.html'
    },
    {
        'title':    'OMT B Classics',
        'url':      BASE_URL + 'b/'
    },
    {
        'title':    'TV',
        'url':      BASE_URL + 'tv/'
    }
]

##########################################################################################
def Start():
    # Setup the default attributes for the ObjectContainer
    ObjectContainer.title1 = TITLE
    ObjectContainer.art    = R(ART)

    # Setup the default attributes for the other objects
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art   = R(ART)

    HTTP.CacheTime             = CACHE_1HOUR
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT

##########################################################################################
@handler(PREFIX, TITLE, thumb = ICON, art = ART)
def MainMenu():
    oc = ObjectContainer()
    
    for category in PREDEFINED_CATEGORIES:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        Items,
                        url = category['url'],
                        category = category['title'],
                        tv = '/tv/' in category['url']
                    ),
                title = category['title']
            )
        )
    
    oc.add(
        DirectoryObject(
            key =
                Callback(
                    AllMovies
                ),
            title = 'All Movies'
        )
    )
        
    return oc

##########################################################################################
@route(PREFIX + '/AllMovies')
def AllMovies():
    oc = ObjectContainer(title2 = "All Movies")
    
    pageElement = HTML.ElementFromURL(BASE_URL)
    
    for item in pageElement.xpath("//*[@class='Normal-C']"):
        url   = BASE_URL + item.xpath(".//a/@href")[0]
        title = ''.join(item.xpath(".//a/text()")).strip()
        
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        Items,
                        url = url,
                        category = title
                    ),
                title = title
            )
        )
    
    return oc
    
##########################################################################################
@route(PREFIX + '/Items', tv = bool) 
def Items(url, category, tv = False):
    oc = ObjectContainer(title2 = category)
    
    originalURL = url
    baseURL     = url[:url.rfind("/") + 1]
    pageElement = HTML.ElementFromURL(url)
    
    # Add movies by parsing the site
    for item in pageElement.xpath("//a"):
        url = item.xpath("./@href")[0]
        
        try:
            thumb = item.xpath(".//img/@src")[0]
        except:
            continue
        
        if not thumb.startswith("http"):
            thumb = baseURL + thumb
            
        if not (url.startswith(baseURL) or '28_00.jpg' in thumb or '14_00.jpg' in thumb) or ' ' in thumb:
            continue
            
        if not url.endswith(".html"):
            continue
        
        count = 3
        if '/b/' in originalURL:
            count = 4
        
        if url.count("/") > count:
            continue
        
        title = url.replace(baseURL, "").replace(".html", "").replace("_", " ").replace("%20", " ").title().strip()
        
        if not url.startswith("http"):
            url = baseURL + url
        
        try:
            altTitle = item.xpath(".//img/@alt")[0].lower().strip()
            if ' ' in altTitle:
                altTitle = altTitle[:altTitle.rfind(' ')]
                
            if title.lower().startswith("page"):
                title = altTitle.title()
        except:
            altTitle = ''
        
        summary = None
        for span in pageElement.xpath("//span"):
            text = span.xpath(".//text()")
            
            try:
                textToSearch = text[0].lower().strip()
            except:
                continue

            match = (title.lower() in textToSearch) or ((altTitle != '') and (altTitle in textToSearch))

            if match and len(text) > 1:
                try:
                    summary = ''.join(text).strip()
                    break
                except:
                    continue
        
        if tv:
            if 'hillbillies' in title.lower() or \
               'outer limits' in title.lower() or \
               'flipper' in title.lower() or \
               'mutual' in title.lower():
                continue
                
            oc.add(
                DirectoryObject(
                    key = Callback(Seasons, url = url, title = title, thumb = thumb),
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(thumb),
                    summary = summary
                )
            )
        else:
            oc.add(
                MovieObject(
                    url = url,
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(thumb),
                    summary = summary
                )
            )
        
    # Add next page(if existing)
    for item in pageElement.xpath("//a"):
        try:
            if 'next page' == item.xpath("./text()")[0].lower():
                url = item.xpath("./@href")[0]
                
                if not url.startswith(baseURL):
                    url = baseURL + url
                
                if url != originalURL: 
                    oc.add(
                        NextPageObject(
                            key = 
                                Callback(
                                    Items,
                                    url = url,
                                    category = category
                                ),
                            title = unicode("More...")
                        )
                    )
                    break
        except:
            continue

    if len(oc) < 1:
        return NoContentFoundMessage(oc, 'Could not find any content for this section')
            
    return oc

##########################################################################################
@route(PREFIX + '/Seasons') 
def Seasons(url, title, thumb):
    oc = ObjectContainer(title2 = title)
    
    pageElement = HTML.ElementFromURL(url)
    
    baseURL = url[:url.rfind("/") + 1]
    for item in pageElement.xpath("//span//a"):
        try:
            url = item.xpath("./@href")[0]
        except:
            continue 
            
        title = ''.join(item.xpath(".//text()")).strip()
        if not title:
            continue
        
        if 'youtube.com/watch' in url:
            element = HTML.ElementFromURL(url)
            
            for link in element.xpath("//a/@href"):
                if '/playlist?list' in link:
                    if not link.startswith('http'):
                        link = 'https://www.youtube.com' + link
                        
                    url = link
        
        if 'youtube.com/playlist' in url or 'youtube.com/user' in url or 'youtube.com/channel' in url:
            finalURL = url
            
            oc.add(
                DirectoryObject(
                    key = Callback(Episodes, url = finalURL, title = title, thumb = thumb),
                    title = title,
                    thumb = thumb
                )
            )
            
        elif url.startswith('page') and url.endswith('.html'):
            finalURL = baseURL + url
            
            oc.add(
                EpisodeObject(
                    url = finalURL,
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(thumb)
                )
            )
            
    if len(oc) < 1:
        return NoContentFoundMessage(oc, 'Could not find any content for this show')
    
    elif len(oc) == 1:
        if 'youtube.com' in finalURL:
            return Episodes(
                url = finalURL,
                title = oc.objects[0].title,
                thumb = oc.objects[0].thumb
            )
        else:
            if URLService.MetadataObjectForURL(oc.objects[0].url):
                return EpisodeObject(
                    url = oc.objects[0].url,
                    title = oc.objects[0].title,
                    thumb = oc.objects[0].thumb
                )

            else:
                return NoContentFoundMessage(oc, 'Could not find any content for this show. Possible block on copyright bounds?') 

    else:
        return oc
    
##########################################################################################
@route(PREFIX + '/Episodes', offset = int) 
def Episodes(url, title, thumb, offset = 0):
    oc = ObjectContainer(title2 = title)

    pageElement = HTML.ElementFromURL(url)
    
    originalURL   = url
    originalTitle = title
    originalThumb = thumb
    baseURL       = url[:url.rfind("/") + 1]
    
    if '/playlist?' in url:
        for item in pageElement.xpath("//*[@class='pl-video yt-uix-tile ']")[offset:]:
            try:
                url = item.xpath(".//@href")[0]
                if not url.startswith("http"):
                    url = baseURL + url
            except:
                continue
            
            try:
                title = item.xpath(".//*[@class='pl-video-title']//a//text()")[0].strip()
                
                try:
                    title = title.split("-")[1].strip()
                except:
                    pass
            except:
                continue
        
            oc.add(
                EpisodeObject(
                    url = url,
                    title = title,
                    thumb = originalThumb
                )
            )
            
            if len(oc) >= EPISODES_PER_PAGE:
                oc.add(
                    NextPageObject(
                        key = 
                            Callback(
                                Episodes,
                                url = originalURL,
                                title = originalTitle,
                                thumb = originalThumb,
                                offset = offset + EPISODES_PER_PAGE
                            ),
                        title = "More..."
                    )
                )
                return oc
    else:
        for item in pageElement.xpath("//li//a")[offset:]:
            try:
                url = item.xpath("./@href")[0]
                
                if not '/watch' in url:
                    continue
                    
                if not url.startswith("http"):
                    url = baseURL + url
            except:
                continue
            
            try:
                title = item.xpath("./@title")[0]
                
                try:
                    title = title.split("-")[1].strip()
                except:
                    pass
            except:
                continue
        
            oc.add(
                EpisodeObject(
                    url = url,
                    title = title,
                    thumb = originalThumb
                )
            )
            
            if len(oc) >= EPISODES_PER_PAGE:
                oc.add(
                    NextPageObject(
                        key = 
                            Callback(
                                Episodes,
                                url = originalURL,
                                title = originalTitle,
                                thumb = originalThumb,
                                offset = offset + EPISODES_PER_PAGE
                            ),
                        title = "More..."
                    )
                )
                return oc  

    
    if len(oc) < 1:
        return NoContentFoundMessage(oc, 'Could not find any episodes for this show')
  
    return oc

##########################################################################################
def NoContentFoundMessage(oc, message):
    oc.header  = "Sorry"
    oc.message = message
  
    return oc    