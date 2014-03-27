TITLE = 'Old Movie Time'
ART   = 'art-default.jpg'
ICON  = 'icon-default.png'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

BASE_URL = "http://oldmovietime.com/"

PREFIX = '/video/oldmovietime'

PREDEFINED_CATEGORIES = [ 
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
                        Movies,
                        url = category['url'],
                        category = category['title']
                    ),
                title = category['title']
            )
        )
        
    return oc
    
##########################################################################################
@route(PREFIX + '/Movies') 
def Movies(url, category):
    oc = ObjectContainer(title2 = category)
    
    originalURL = url
    pageElement = HTML.ElementFromURL(url)
    
    # Add movies by parsing the site
    for item in pageElement.xpath("//a"):
        url = item.xpath("./@href")[0]
        
        try:
            thumb = item.xpath(".//img/@src")[0]
        except:
            continue
        
        if not thumb.startswith("http"):
            thumb = BASE_URL + thumb
            
        if not (url.startswith(BASE_URL) or '28_00.jpg' in thumb):
            continue
            
        if not url.endswith(".html"):
            continue
        
        if url.count("/") > 3:
            continue
        
        if not url.startswith("http"):
            url = BASE_URL + url
            
        title = url.replace(BASE_URL, "").replace(".html", "").replace("_", " ").replace("%20", " ").title().strip()
        
        try:
            altTitle = item.xpath(".//img/@alt")[0].lower().strip()
            if ' ' in altTitle:
                altTitle = altTitle[:altTitle.rfind(' ')]
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
        
        oc.add(
            MovieObject(
                url = url,
                title = title,
                thumb = thumb,
                summary = summary
            )
        )
        
    # Add next page(if existing)
    for item in pageElement.xpath("//a"):
        try:
            if 'next page' == item.xpath("./text()")[0].lower():
                url = item.xpath("./@href")[0]
                
                if not url.startswith(BASE_URL):
                    url = BASE_URL + url
                
                if url != originalURL: 
                    oc.add(
                        NextPageObject(
                            key = 
                                Callback(
                                    Movies,
                                    url = url,
                                    category = category
                                ),
                            title = unicode("Next page...")
                        )
                    )
                    break
        except:
            continue

    if len(oc) < 1:
        oc.header  = unicode("Sorry")
        oc.message = unicode("Could not find any content")
            
    return oc



