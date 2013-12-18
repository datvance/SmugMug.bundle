DEBUG = False

PREFIX = "/photos/smugmug"
NAME = "SmugMug"

ART = R("art-default.jpg")
ICON = R("icon-default.png")

NAMESPACES = {"media": "http://search.yahoo.com/mrss/"}

POPULAR_FEED = "http://www.smugmug.com/hack/feed.mg?Type=popular&Data=%s&format=rss200"
POPULAR_FEEDS = {"today": "Today's Most Popular", "all": "All-Time Most Popular"}

FAVORITE_FEED = "http://%s.smugmug.com/hack/feed.mg?Type=%s&Data=%s&format=rss200"
FAVORITE_FEEDS = {"nicknameRecentPhotos": "Recent Photos",
                  "recentVideos": "Recent Videos",
                  "nickname": "Galleries"}


####################################################################################################
def Start():

    Plugin.AddViewGroup("Pictures", viewMode="Pictures", mediaType="photos")
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")

    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = NAME
    ObjectContainer.art = ART
    ObjectContainer.view_group = "InfoList"

    DirectoryObject.thumb = ICON

    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36"

    Dict.Reset()


####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    oc = ObjectContainer()

    for item in POPULAR_FEEDS.keys():
        oc.add(DirectoryObject(key=Callback(ListPhotos, which=item), title=POPULAR_FEEDS[item], thumb=ICON))

    for i in range(1, 10):
        nickname = Prefs["favorite-%d" % i]
        log("nickname %d: %s" % (i, nickname))
        if nickname is not None:
            title = "Favorite: %s" % nickname
            oc.add(DirectoryObject(key=Callback(GetFavorite, query=nickname), title=title, thumb=ICON))

    oc.add(PrefsObject(title="Preferences", summary="Add Favorites", thumb=R("icon-prefs.png")))

    return oc


####################################################################################################
@route(PREFIX + '/list-photos')
def ListPhotos(which):

    if which in POPULAR_FEEDS:
        url = POPULAR_FEED % which

    elif which.startswith("http"):
        # a gallery
        src = HTML.ElementFromURL(which)
        rss = src.xpath("//link[@type='application/rss+xml']/@href")[0]
        url = "http://www.smugmug.com" + rss
    else:
        # recent photos from a favorite
        url = FAVORITE_FEED % (which, "nicknameRecentPhotos", which)

    feed = XML.ElementFromURL(url)

    title = feed.xpath("//rss/channel/title")[0].text

    oc = ObjectContainer(view_group="InfoList", title1=title)

    for item in feed.xpath("//rss/channel//item"):

        details = GetItemDetails(item)
        if details is not False:
            oc.add(CreatePhotoObject(details))

    return oc


####################################################################################################
@route(PREFIX + '/list-galleries')
def ListGalleries(nickname):

    url = FAVORITE_FEED % (nickname, "nickname", nickname)

    feed = XML.ElementFromURL(url)
    title = feed.xpath("//rss/channel/title")[0].text
    oc = ObjectContainer(view_group="InfoList", title1=title)

    for item in feed.xpath("//rss/channel//item"):

        details = GetItemDetails(item)
        if details is not False:
            oc.add(DirectoryObject(key=Callback(ListPhotos, which=details["link"]),
                                   title=details["title"], thumb=details["thumb"]))

    return oc


####################################################################################################
# query should be a SmugMug nickname, e.g. nickname.smugmug.com
@route(PREFIX + '/get-favorite')
def GetFavorite(query):

    oc = ObjectContainer(view_group="InfoList", title1="Favorite: " + query)

    for feed in FAVORITE_FEEDS:
        try:
            url = FAVORITE_FEED % (query, feed, query)
            title = "%s For %s" % (FAVORITE_FEEDS[feed], query)
            log("Retrieving " + title)
            item = XML.ElementFromURL(url).xpath("//rss/channel//item")[0]

            details = GetItemDetails(item)
            if details is False:
                continue

            if feed == "nicknameRecentPhotos":
                oc.add(DirectoryObject(key=Callback(ListPhotos, which=query),
                                       title=title, thumb=details["thumb"]))
            elif feed == "nickname":
                oc.add(DirectoryObject(key=Callback(ListGalleries, nickname=query),
                                       title=title, thumb=details["thumb"]))
        except:
            continue

    if len(oc.objects) < 1:
        return ObjectContainer(header="Error", message="No Photos or Videos Found for %s" % query)
    else:
        return oc


####################################################################################################
@route(PREFIX + '/get-item-details')
def GetItemDetails(item):

    try:
        details = {}

        details["title"] = item.xpath("./title")[0].text

        details["guid"] = item.xpath("./guid")[0].text

        details["link"] = item.xpath("./guid")[0].text

        description = item.xpath("./description")[0].text.replace('&gt;', '>').replace('&lt', '<')
        details["summary"] = String.StripTags(description)

        date = item.xpath("./pubDate")[0].text
        details["date"]= Datetime.ParseDate(date)

        details["category"] = item.xpath("./category")[0].text

        try:
            imgs = item.xpath(".//media:content/@url", namespaces=NAMESPACES)
            if len(imgs) > 0:
                details["img"] = imgs[-1]
                details["thumb"] = details["guid"]
        except:
            pass

        if "img" not in details:
            details["img"] = False
            details["thumb"] = HTML.ElementFromString(description).xpath("//img/@src")[0]

        log(str(details))
        return details

    except:
        return False


####################################################################################################
@route(PREFIX + '/create-photo-object')
def CreatePhotoObject(details, container=False):

    obj = PhotoObject(
        key=Callback(
            CreatePhotoObject,
            details,
            container=True
        ),
        rating_key=details["thumb"],
        title=details["title"],
        summary=details["summary"],
        thumb=details["thumb"],
        originally_available_at=details["date"],
        items=[MediaObject(parts=[PartObject(key=Callback(GetPhoto, img=details["img"]))])]
    )

    if container:
        return ObjectContainer(objects=[obj])
    else:
        return obj


####################################################################################################
@route(PREFIX + '/get-photo')
def GetPhoto(img):
    return Redirect(img)


####################################################################################################
def log(msg):
    if DEBUG:
        Log.Debug(msg)