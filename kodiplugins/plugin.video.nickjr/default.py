# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, base64, re, gzip, json, os, math, time
from StringIO import StringIO
import urllib, urllib2, urlparse
from AdvancedHTMLParser.Parser import AdvancedHTMLParser

AddonID = 'plugin.video.nickjr'
Addon = xbmcaddon.Addon(AddonID)
icon = Addon.getAddonInfo('icon')
handle = int(sys.argv[1])
baseUrl = 'http://nickjr.walla.co.il/'
userDir = xbmc.translatePath(Addon.getAddonInfo("profile")).decode("utf-8")

import threading


class Thread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
    def run(self):
        self._target(*self._args)

def GetSeriesList():
	text = OpenURL(baseUrl)
	block = re.compile('padding: 10px(.*?)folder2_game', re.S).findall(text)
	page = re.compile('<a href="(.*?)".*?0px;">(.*?)<').findall(block[0])
	for path in page:
		url=path[0]
		name = path[1].decode('windows-1255').encode('utf-8')
		#text2 = OpenURL(url)
		#img = re.compile('class="stripe_title w7b white">.*?>(.*?)<.*?src="(.*?)"', re.S).findall(text2)[0][1]
		addDir(name, url, 1, None)
		
def GetEpisodesList(url):
	text = OpenURL(baseUrl + url)
	#additional_urls = re.compile('<a href="(.+?)" class="in_blk channel"').findall(text)
	#if url in additional_urls:
	#	additional_urls.remove(url)
	#for u in additional_urls:
	#	text+=OpenURL(baseUrl + u)
	urls = re.compile('<div class="title w4b"><a href="(.*?)"', re.S).findall(text)
	urls += re.compile('<div class="title w5b mt5"><a href="(.*?)"', re.S).findall(text)
	threads = []
	
	def work(path):	
		data = OpenURL(baseUrl + path + '/@@/video/flv_pl')
		titleMatches = re.compile('<title>(.*?)</title>(.*)<subtitle>(.*?)<', re.S).findall(data)
		title = titleMatches[0][0]
		subtitle = titleMatches[0][2]
		images = re.compile('<preview_pic>(.*?)</preview_pic>', re.S).findall(data)
		if (len(images)) >= 1:
		    iconImage = images[0]
		details = re.compile('<synopsis>(.*?)</synopsis>', re.S).findall(data)[0]
		try:
			details2 = details.decode('windows-1255').encode('utf-8')
		except:
			details2 = details
		timeInSeconds = re.compile('<duration>(.*?)</duration>', re.S).findall(data)
		if not timeInSeconds == None and not len(timeInSeconds[0]) <= 0:
		    time = int(timeInSeconds[0]) / 60
		else:
		    time = '00:00'
		
		url='http://62.90.90.56/walla_vod/_definst_/'+ re.compile('<src>(.*?)</src>', re.S).findall(data)[0]+'.mp4/playlist.m3u8'
		addDir(title, url, 3, iconImage, infos={'subtitle':subtitle, 'details':details2, 'length':str(time)})
		
	for path in urls:
		threads.append(Thread(work, path))
	[i.start() for i in threads]
	
	while True:
		is_alive = [x.is_alive() for x in threads]
		print is_alive
		if all(x == False for x in is_alive): break
		time.sleep(0.1)
		
	
	
def Play(name, url, iconimage):
	listItem = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=listItem)

def OpenURL(url, headers={}, user_data={}, referer=None, Host=None):
	print 'Opening url {}'.format(url)
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
	GetSeriesList()
elif mode == 1:
	# "------------ Episodes: ----------------"
	GetEpisodesList(url)
elif mode == 3:
	# "-------- Playing episode  -------------"
	Play(name, url, iconimage)
elif mode == 4:
	# "- Move to a specific episodes' page	 --"
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