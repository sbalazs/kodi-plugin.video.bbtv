# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
from urllib import urlencode
from urlparse import parse_qsl
import urllib2
import re
import xbmcaddon
import xbmcgui
import xbmcplugin

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

bbtv_video_url_base = 'http://www.bbtv.hu/'
bbtv_video_list_url = bbtv_video_url_base + 'videok'

def load_url(url):
    try:
        req = urllib2.Request(url, None, {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5','Accept-Language': 'hu-HU,hu;q=0.8'})
        url_handler = urllib2.urlopen(req)
        url_content = url_handler.read()
        url_handler.close()
    except:
        url_content = 'ERROR'
        addon = xbmcaddon.Addon()
        addonname = addon.getAddonInfo('name')
        line1 = u'Cannot connect to URL ' + url + '!'
        xbmcgui.Dialog().ok(addonname, line1)
        return url_content
    return url_content

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_videos():
    html_content = load_url(bbtv_video_list_url)
    return re.compile('<div class="search-result-item">\n\s+<img src="([-_a-zA-Z0-9\.\/\:]+)".*\n.*>([-a-zA-Z0-9\s\#\.]+)<\/a></h4>\n\s+<p>(.*\n?.*)</p>\n\s+<a class="search-link" href="([-_a-zA-Z0-9\.\/\:]+)"').findall(html_content)

def list_videos():
    """
    Create the list of playable videos in the Kodi interface.
    """
    videos = get_videos()
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem()
        # Set additional info for the list item.
        list_item.setInfo('video', {'title': video[1], 'plot': video[2]})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video[0], 'icon': video[0], 'fanart': video[0]})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        url = get_url(action='play', video=video[3])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    video_page_html = load_url(bbtv_video_url_base + path)
    vimeo_url = re.compile('<meta property="og:video:url" content="([-_=a-zA-Z0-9\:\/\.\?]+)"').findall(video_page_html)
    vimeo_page_html = load_url(vimeo_url[0])
    video_url = re.compile('"progressive":\[{"profile":[-a-zA-Z0-9\,\:\"\/]+"url":"([-_=a-zA-Z0-9\:\/\.\?]+)"').findall(vimeo_page_html)

    play_item = xbmcgui.ListItem(path=video_url[0])

    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_videos()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
