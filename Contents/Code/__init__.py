DEBUG = False

PREFIX = "/photos/smugmug"
NAME = "SmugMug"

ART = R("art-default.jpg")
ICON = R("icon-default.png")

NAMESPACES = {"media": "http://search.yahoo.com/mrss/"}

POPULAR_FEED = "http://www.smugmug.com/hack/feed.mg?Type=popular&Data=%s&format=rss200"
POPULAR_FEEDS = {"today": "Today's Most Popular", "all": "All-Time Most Popular"}

FAVORITE_FEED = "http://%s.smugmug.com/hack/feed.mg?Type=%s&Data=%s&format=rss200"
FAVORITE_FEEDS = {"nicknameRecentPhotos": "Recent Photos", "recentVideos": "Recent Videos"}

FAVORITE_KEY = "SMUGMUG_FAVORITES"
#{'familyvance': {}}

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

    if FAVORITE_KEY not in Dict:
        Dict[FAVORITE_KEY] = {}
    else:
        log(str(Dict[FAVORITE_KEY]))

####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    oc = ObjectContainer()

    for item in POPULAR_FEEDS.keys():
        oc.add(DirectoryObject(key=Callback(ListPhotos, which=item), title=POPULAR_FEEDS[item], thumb=ICON))

    if FAVORITE_KEY in Dict:
        for nickname in Dict[FAVORITE_KEY]:
            title = "Favorite: %s" % nickname
            oc.add(DirectoryObject(key=Callback(GetFavorite, query=nickname), title=title, thumb=ICON))

    # on plex/web this just shows up as a search box. sucks
    oc.add(InputDirectoryObject(key=Callback(GetFavorite), title="Add Favorite", prompt="SmugMug Nickname"))

    return oc


####################################################################################################
@route(PREFIX + '/list-photos')
def ListPhotos(which):

    oc = ObjectContainer(view_group="InfoList", title1=which)

    if which in POPULAR_FEEDS:
        url = POPULAR_FEED % which
    else:
        url = FAVORITE_FEED % (which, "nicknameRecentPhotos", which)

    feed = XML.ElementFromURL(url)
    for item in feed.xpath("//rss/channel//item"):

        details = GetItemDetails(item)
        if details is not False:
            oc.add(CreatePhotoObject(details))

    return oc


####################################################################################################
# query can be either a search from "add favorite" or a nickname from favorites list
@route(PREFIX + '/get-favorite')
def GetFavorite(query):

    oc = ObjectContainer(view_group="InfoList", title1=query)

    for feed in FAVORITE_FEEDS:
        try:
            url = FAVORITE_FEED % (query, feed, query)
            item = XML.ElementFromURL(url).xpath("//rss/channel//item")[0]
            details = GetItemDetails(item)
            title = "%s For %s" % (FAVORITE_FEEDS[feed], query)
            oc.add(DirectoryObject(key=Callback(ListPhotos, which=query),
                               title=title, thumb=details["thumb"]))
        except:
            continue

    if len(oc.objects) < 1:
        return ObjectContainer(header="Error", message="No Photos or Videos Found for %s" % nickname)

    # if not in dict, save it, otherwise give them option to remove it
    if query not in Dict[FAVORITE_KEY]:
        Dict[FAVORITE_KEY][query] = {}  # future expansion!
        Dict.Save()
        log("Saved favorite: %s" % query)
    else:
        oc.add(DirectoryObject(key=Callback(RemoveFavorite, nickname=query), title="Remove Favorite"))

    return oc


####################################################################################################
@route(PREFIX + '/get-item-details')
def GetItemDetails(item):

    try:
        details = {}

        details["thumb"] = item.xpath("./guid")[0].text
        details["title"] = item.xpath("./title")[0].text

        summary = item.xpath("./description")[0].text.replace('&gt;', '>').replace('&lt', '<')
        details["summary"] = String.StripTags(summary.replace("<br />", " - ", 1))

        date = item.xpath("./pubDate")[0].text
        details["date"]= Datetime.ParseDate(date)

        details["img"] = item.xpath(".//media:content/@url", namespaces=NAMESPACES)[-1]

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
@route(PREFIX + '/remove-favorite')
def RemoveFavorite(nickname):
    if nickname in Dict[FAVORITE_KEY]:
        Dict[FAVORITE_KEY][nickname] = None
        del Dict[FAVORITE_KEY][nickname]

    return ObjectContainer(header="Success", message="The %s Favorite has been removed." % nickname)


####################################################################################################
def log(msg):
    if DEBUG:
        Log.Debug(msg)