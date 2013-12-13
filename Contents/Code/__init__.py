DEBUG = False

PREFIX = "/photos/smugmug"
NAME = "SmugMug"

ART = R("art-default.jpg")
ICON = R("SmugMugLogo.png")

SMUGMUG_FEEDS = {
    "Today's Most Popular": "http://www.smugmug.com/hack/feed.mg?Type=popular&Data=today&format=rss200",
    "All-Time Most Popular": "http://www.smugmug.com/hack/feed.mg?Type=popular&Data=all&format=rss200"
}
NAMESPACES = {"media": "http://search.yahoo.com/mrss/"}


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


####################################################################################################
@handler(PREFIX, NAME)
def MainMenu():

    oc = ObjectContainer()

    for item in SMUGMUG_FEEDS:
        oc.add(DirectoryObject(key=Callback(ListPhotos, which=item), title=item, thumb=ICON))

    return oc


####################################################################################################
@route(PREFIX + '/list-photos')
def ListPhotos(which):

    oc = ObjectContainer(view_group="InfoList", title1=which)

    url = SMUGMUG_FEEDS[which]

    details = {}
    feed = XML.ElementFromURL(url)
    for item in feed.xpath("//rss/channel//item"):

        try:
            details["thumb"] = item.xpath("./guid")[0].text
            details["title"] = item.xpath("./title")[0].text

            summary = item.xpath("./description")[0].text.replace('&gt;', '>').replace('&lt', '<')
            details["summary"] = String.StripTags(summary.replace("<br />", " - ", 1))

            date = item.xpath("./pubDate")[0].text
            details["date"]= Datetime.ParseDate(date)

            details["img"] = item.xpath(".//media:content/@url", namespaces=NAMESPACES)[-1]

            oc.add(CreatePhotoObject(details))

        except:
            continue

    return oc


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


def GetPhoto(img):
    return Redirect(img)


####################################################################################################
def log(str):
    if DEBUG:
        Log.Debug(str)