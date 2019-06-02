import re

TITLE = 'Crackle'

TYPE_MOVIES = 'movies'
TYPE_TELEVISION = 'shows'

GENRE_ALL = 'all'
GENRE_ACTION = '2'
GENRE_COMEDY = '18'
GENRE_THRILLER = '58'
GENRE_ANIME="8"
GENRE_DRAMA="23"
GENRE_ORIGINAL="324"
GENRE_ICON="328"




URL_GEO = 'http://web-api-us.crackle.com/Service.svc/geo/country?format=json'
URL_CATEGORIES = 'http://web-api-us.crackle.com/Service.svc/browse/%s/all/%s/alpha-asc/%s/20/1?format=json'
URL_DETAILS = 'http://ios-api.crackle.com/Service.svc/channel/%s/folders/%s?format=json'
URL_MEDIA_DETAILS = 'http://ios-api.crackle.com/Service.svc/details/media/%s/%s?format=json'

###################################################################################################
def Start():

  Plugin.AddViewGroup('List', viewMode = 'List', mediaType = 'items')
  Plugin.AddViewGroup('InfoList', viewMode = 'InfoList', mediaType = 'items')

  ObjectContainer.title1 = TITLE
  ObjectContainer.view_group = 'List'

  HTTP.CacheTime = CACHE_1DAY

###################################################################################################
@handler('/video/crackle', TITLE)
def MainMenu():

  # Determine the location of the client, and the associated API region code
  location_details = JSON.ObjectFromURL(URL_GEO)

  if location_details['status']['messageCode'] != '0':
    return MessageContainer(location_details['status']['message'])

  location = location_details['CountryCode']

  oc = ObjectContainer()

  oc.add(DirectoryObject(key = Callback(Genres, title = 'Movies', type = TYPE_MOVIES, location = location), title = 'Movies'))
  oc.add(DirectoryObject(key = Callback(Genres, title = 'Television', type = TYPE_TELEVISION, location = location), title = 'Television'))

  # This is currently disabled as it appears that they're still working on it. I originally didn't get any titles, now I get titles
  # which have no associated information.
  # oc.add(DirectoryObject(key = Callback(Genres, title = 'Collections', type = TYPE_COLLECTIONS, location = location), title = 'Collections'))

  return oc

###################################################################################################
def Genres(title, type, location):

  oc = ObjectContainer(title2 = title)

  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'All Genres', type = type, genre = GENRE_ALL, location = location), title = 'All Genres'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Action', type = type, genre = GENRE_ACTION, location = location), title = 'Action'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Comedy', type = type, genre = GENRE_COMEDY, location = location), title = 'Comedy'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Thriller', type = type, genre = GENRE_THRILLER, location = location), title = 'Thriller'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Anime', type = type, genre = GENRE_ANIME, location = location), title = 'Anime'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Drama', type = type, genre = GENRE_DRAMA, location = location), title = 'Drama'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Crackle Originals', type = type, genre = GENRE_ORIGINAL, location = location), title = 'Crackle Originals'))
  oc.add(DirectoryObject(key = Callback(ListChannels, title = 'Icon', type = type, genre = GENRE_ICON, location = location), title = 'Icon'))


  return oc

###################################################################################################
def ListChannels(title, type, genre, location):

  oc = ObjectContainer(title2 = title, view_group = 'InfoList')
  titles = JSON.ObjectFromURL(URL_CATEGORIES % (type, genre, location))

  for title in titles['Entries']:

    oc.add(DirectoryObject(
      key = Callback(ListTitles, title = title['Name'], id = title['ID'], location = location), 
      title = title['Name'],
      summary = title['Description'],
      thumb = title['ChannelArtTileLarge']
    ))

  if len(oc) < 1:
    return ObjectContainer(header="Error", message="No titles were found!")

  return oc

###################################################################################################
def ListTitles(title, id, location):

  oc = ObjectContainer(title2 = title, view_group = 'InfoList')
  titles = JSON.ObjectFromURL(URL_DETAILS % (id, location))

  if len(titles['FolderList']) == 0:
    return MessageContainer("Error", "No titles were found!")

  for playlist in titles['FolderList'][0]['PlaylistList']:
    for title in playlist['MediaList']:
      url = title['DetailsURL']
      video_title = title['Title']
      summary = title['Description']
      thumb = title['ThumbnailExternal']
      genres = [ genre.strip() for genre in title['Genre'].split(',') ]
      content_rating = title['Rating']
      date = Datetime.ParseDate(title['ReleaseDate'])

      duration_text = title['Duration']
      duration_dict = re.match("((?P<hours>[0-9]+):)?(?P<mins>[0-9]+):(?P<secs>[0-9]+)", duration_text).groupdict()

      hours = 0
      if duration_dict['hours'] != None:
          hours = int(duration_dict['hours'])

      mins = int(duration_dict['mins'])
      secs = int(duration_dict['secs'])
      duration = ((((hours * 60) + mins) * 60) + secs) * 1000

      if title['RootChannel'] == 'Movies':
        oc.add(MovieObject(
          url = url,
          title = video_title,
          summary = summary,
          thumb = thumb,
          genres = genres,
          content_rating = content_rating,
          duration = duration,
          originally_available_at = date
        ))

      elif title['RootChannel'] == 'Television' or title['RootChannel'] == 'Originals':

        show = title['ParentChannelName']

        try: season = int(title['Season'])
        except: season = None

        try: index = int(title['Episode'])
        except: index = None

        oc.add(EpisodeObject(
          url = url,
          show = show,
          title = video_title,
          season = season,
          index = index,
          summary = summary,
          thumb = thumb,
          content_rating = content_rating,
          duration = duration,
          originally_available_at = date
        ))

  return oc
