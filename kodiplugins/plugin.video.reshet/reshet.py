# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, base64, re, gzip, json, os, math
from StringIO import StringIO
import urllib, urllib2, urlparse
from AdvancedHTMLParser.Parser import AdvancedHTMLParser

AddonID = 'plugin.video.reshet'
Addon = xbmcaddon.Addon(AddonID)
icon = Addon.getAddonInfo('icon')
handle = int(sys.argv[1])
baseUrl = 'http://reshet.tv/Shows/Vod/'
userDir = xbmc.translatePath(Addon.getAddonInfo("profile")).decode("utf-8")

def GetSeriesList(id, name):
	url = baseUrl
	text = OpenURL(url)	
	parser = AdvancedHTMLParser()
	parser.feed(text)
	elm = parser.getElementById('contentFull')
	tags = parser.getElementsByClassName('trippleRowItem', elm)
	for tag in tags:
		url = tag.children[0].attributes['href']
		name = tag.children[0].children[0].children[1].children[0].text
		img = tag.children[0].children[0].children[0].children[0].children[1].attributes['src']
		addDir(name, url, 1, img)
		
def GetSectionsList(url, iconimage):
	text = OpenURL(url)	
	matches = re.compile('var gc_arr_(.) = (.+?)\n').findall(text)
	for id, match in matches:
		j = json.loads(match[:-1])
		title = j[0]['Title']
		parser = AdvancedHTMLParser()
		parser.feed(title)
		name = parser.root.children[0].text.encode('utf-8')
		img = j[0]['Image']
		url = j[0]['Item_URL']
		addDir(name, url, 2, img)
		

def GetEpisodesList(url, iconimage):
	text = OpenURL(url)	
	matches = re.compile('var items = (.+?)\n').findall(text)
	j = json.loads(matches[0][:-1])
	for item in j:
		name = item['Title'].encode('utf-8')
		img = item['Image']
		url = item['Item_URL']		
		addDir(name, url, 3, img, item)

def Play(name, url, iconimage):
	text = OpenURL(url)	
	id = re.compile('build_player\(.+?, (.+?), .+?\)').findall(text)[0][1:-1]
	listItem = xbmcgui.ListItem(path='http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId={}'.format(id))
	xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=listItem)

def OpenURL(url, headers={}, user_data={}, referer=None, Host=None):
	link = ""
	if user_data:
		user_data = urllib.urlencode(user_data)
		req = urllib2.Request(url, user_data)
	else:
		req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36')
	req.add_header('Accept-encoding', 'gzip')
	for k, v in headers.items():
		req.add_header(k, v)
	if referer:
		req.add_header('Referer' ,referer)
	if Host:
		req.add_header('Host' ,Host)
	try:
		response = urllib2.urlopen(req,timeout=100)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			link = f.read()
		else:
			link = response.read()
		response.close()
	except Exception as ex:
		xbmc.log('{0}'.format(ex), 3)
		return None
	return link
		
def addDir(name, url, mode, iconimage, infos={}, totalItems=None, isFolder=True):
	u = "{0}?url={1}&mode={2}&name={3}&iconimage={4}".format(sys.argv[0], urllib.quote_plus(url), str(mode), urllib.quote_plus(name), iconimage)

	if (iconimage == None):
		iconimage = "DefaultFolder.png"
		
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo(type="Video", infoLabels=infos)
	if mode==3:
		isFolder=False
		liz.setProperty("IsPlayable","true")
	if totalItems == None:
		ok = xbmcplugin.addDirectoryItem(handle=handle,url=u,listitem=liz,isFolder=isFolder)
	else:
		ok =xbmcplugin.addDirectoryItem(handle=handle,url=u,listitem=liz,isFolder=isFolder,totalItems=totalItems)
	
	return ok
	
def DelCookies():
	try:
		tempDir = xbmc.translatePath('special://temp/').decode("utf-8")
		tempCookies = os.path.join(tempDir, 'cookies.dat')
		if os.path.isfile(tempCookies):
			os.unlink(tempCookies)
	except Exception as ex:
		xbmc.log('{0}'.format(ex), 3)
	
def GetIndexFromUser(title, listLen):
	return 1
# 	dialog = xbmcgui.Dialog()
# 	location = dialog.input('{0} (1-{1})'.format(title, listLen), type=xbmcgui.INPUT_NUMERIC)
# 	if location is None or location == "":
# 		return 1
# 	try:
# 		location = int(location)
# 		if location > listLen or location < 1:
# 			return 1
# 	except:
# 		return 1
# 	return location
	
def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = paramstring
		cleanedparams = params.replace('?','')
		if (params[len(params)-1] == '/'):
			params = params[0:len(params)-2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0].lower()] = splitparams[1]
	return param


xbmcplugin.items = []	
params=get_params()
print params
url = None
mode = None
name = None
iconimage = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:        
	mode = int(params["mode"])
except:
	pass
try:      
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:        
	iconimage = urllib.unquote_plus(params["iconimage"])
except:
	pass
	

if mode == None or url == None or len(url) < 1:
	# "------------- Series: -----------------"
	GetSeriesList(url, name)
elif mode == 1:
	# "------------ Sections: ----------------"
	GetSectionsList(url, iconimage)
elif mode == 2:
	# "------------ Episodes: ----------------"
	GetEpisodesList(url, iconimage)
elif mode == 3:
	# "-------- Playing episode  -------------"
	Play(name, url, iconimage)
elif mode == 4:
	# "- Move to a specific episodes' page  --"
	prms = urlparse.parse_qs(urlparse.urlparse(url).query)
	index = GetIndexFromUser(name, int(prms['Pages'][0]))
	GetEpisodesList('{0}&PageNumber={1}'.format(url[:url.find('&PageNumber=')], index), iconimage)

if mode == 0:
	xbmcplugin.setContent(handle, 'videos')
	xbmc.executebuiltin("Container.SetViewMode(500)")
else:
	xbmcplugin.setContent(handle, 'episodes')
	xbmc.executebuiltin("Container.SetViewMode(504)")

xbmcplugin.endOfDirectory(handle)