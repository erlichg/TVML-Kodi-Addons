# -*- coding: utf-8 -*-

'''
Created on 30/04/2011

@author: shai
'''
__USERAGENT__ = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36'
#__USERAGENT__ = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)'
#DOMAIN='http://www.sdarot.co.in'


import urllib,urllib2,re,xbmc,xbmcplugin,xbmcgui,xbmcaddon,os,sys,time, socket
import StringIO
import gzip
import json
from operator import itemgetter, attrgetter
from proxy import PROXY_PORT
import cloudflare

__settings__ = xbmcaddon.Addon(id='plugin.video.sdarot.tv')
__language__ = __settings__.getLocalizedString
__cachePeriod__ = __settings__.getSetting("cache")
__PLUGIN_PATH__ = __settings__.getAddonInfo('path')
__DEBUG__ = __settings__.getSetting("DEBUG") == "true"
#__DEBUG__ = False

DOMAIN = __settings__.getSetting("domain")
HOST = DOMAIN[7:]
#PROXY_PORT = 9899

#print "common domain=" +  DOMAIN
#print "common domain="+ HOST

__REFERER__ = DOMAIN+'/templates/frontend/blue_html5/player/jwplayer.flash.swf'

def LOGIN():
	#print("LOGIN  is running now!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
	loginurl = DOMAIN+'/login'
	if __settings__.getSetting('username')=='':
		dialog = xbmcgui.Dialog()
		xbmcgui.Dialog().ok('Sdarot','www.sdarot.tv התוסף דורש חשבון  חינמי באתר' ,' במסך הבא יש להכניס את שם המשתמש והסיסמא')
		search_entered = ''
		keyboard = xbmc.Keyboard(search_entered, 'נא הקלד שם משתמש')
		keyboard.doModal()
		if keyboard.isConfirmed():
			search_entered = keyboard.getText() 
		__settings__.setSetting('username',search_entered)
		
	if __settings__.getSetting('user_password')=='':
		search_entered = ''
		keyboard = xbmc.Keyboard(search_entered, 'נא הקלד סיסמא')
		keyboard.doModal()
		if keyboard.isConfirmed():
			search_entered = keyboard.getText()
		__settings__.setSetting('user_password',search_entered)

	username = __settings__.getSetting('username')
	password = __settings__.getSetting('user_password')
	if not username or not password:
		print "Sdarot tv:no credencials found skipping login"
		return
	
	print "Trying to login to sdarot tv site username:" + username
	page = getData(url=loginurl,timeout=0,postData="username=" + username + "&password=" + password +"&submit_login=התחבר",referer=DOMAIN);
   
def CHECK_LOGIN():
	# check's if login  is required.
	#print "check if logged in already"
	if __settings__.getSetting('username').strip() == '' or __settings__.getSetting('user_password') == '':
		return
		
	page = getData(DOMAIN+'/series',referer=DOMAIN)
	#print page
	match = re.compile('<span class="button blue" id="logout"><a href=".*?/log(.*?)">').findall(page)
	#print match
	if match:
		if str(match[0])!='out':
		#	print "login required"
			LOGIN()
		#else:
		#	print "already logged in."
	else:
		LOGIN()
 
def enum(**enums):
		return type('Enum', (), enums)

def getMatches(url, pattern):
		page = getData(url)
		matches=re.compile(pattern).findall(page)
		return matches   

def getParams(arg):
		param=[]
		paramstring=arg
		if len(paramstring)>=2:
			params=arg
			cleanedparams=params.replace('?','')
			if (params[len(params)-1]=='/'):
				params=params[0:len(params)-2]
			pairsofparams=cleanedparams.split('&')
			param={}
			for i in range(len(pairsofparams)):
				splitparams={}
				splitparams=pairsofparams[i].split('=')
				if (len(splitparams))==2:	
					param[splitparams[0]]=splitparams[1]
								
		return param
	
def addDir(name, url, mode, iconimage='DefaultFolder.png', elementId=None, summary='', fanart='',contextMenu=None, isFolder=True):
		u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + name+ "&summary=" + urllib.quote_plus(summary)
		if not elementId == None and not elementId == '':
			u += "&module=" + urllib.quote_plus(elementId)
		liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
		liz.setInfo(type="Video", infoLabels={ "Title": urllib.unquote(name), "Plot": UnEscapeXML(urllib.unquote(summary))})
		
		if not contextMenu == None:
			liz.addContextMenuItems(items=contextMenu, replaceItems=False)

		if not fanart == '':
			liz.setProperty("Fanart_Image", fanart)
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)
		return ok

def addVideoLink(name, url, mode, iconimage='DefaultFolder.png', summary = '', contextMenu=True):
		u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + "&summary=" + urllib.quote_plus(summary)
		liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
		liz.setInfo(type="Video", infoLabels={ "Title": urllib.unquote(name), "Plot": UnEscapeXML(urllib.unquote(summary))})	
		liz.setProperty('IsPlayable', 'true')
		if contextMenu:
			liz.addContextMenuItems(items=[(__language__(30005).encode('utf-8'), 'XBMC.Container.Update({0})'.format(u.replace('mode=4', 'mode=8')))])
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
		return ok
	
def addLink(name, url, iconimage='DefaultFolder.png', sub=''):
		liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo(type="Video", infoLabels={ "Title": urllib.unquote(name), "Plot": urllib.unquote(sub)})
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
		return ok

def extractFromZip(gzipData):
	data = StringIO.StringIO(gzipData)
	gzipper = gzip.GzipFile(fileobj=data)
	html = gzipper.read()
	gzipper.close()
	return html
	
def getData_attempt(url, timeout=__cachePeriod__, name='', postData=None,referer=__REFERER__):
		#print 'getData: url --> ' + url + '\npostData-->' + str(postData)
		if __DEBUG__:
			print 'name --> ' + name
		#temporary disabled the cache - cause problems with headers	
		if timeout > 9999999:
			if name == '':
				cachePath = xbmc.translatePath(os.path.join(__PLUGIN_PATH__, 'cache', 'pages', urllib.quote(url,"")))
			else:
				cachePath = xbmc.translatePath(os.path.join(__PLUGIN_PATH__, 'cache', 'pages', name))
			if (os.path.exists(cachePath) and (time.time()-os.path.getmtime(cachePath))/60/60 <= float(timeout)):
				f = open(cachePath, 'r')
				ret = f.read()
				f.close()
				if __DEBUG__:
					print 'returned data from cache'
				return ret
		socket.setdefaulttimeout(15)
		req = urllib2.Request(url)
		req.add_header('User-Agent', __USERAGENT__)   
		req.add_header('X-Requested-With','XMLHttpRequest')
		req.add_header('Accept','application/json, text/javascript, */*; q=0.01')
		req.add_header('Accept-Encoding','gzip,deflate,sdch')
		req.add_header('Content-Type','application/x-www-form-urlencoded; charset=UTF-8')
		req.add_header('Connection','keep-alive')
		req.add_header('Host',HOST)
		req.add_header('Origin',DOMAIN)
		if (postData):
			req.add_header('Content-Length',len(postData))
		
		if referer: 
			req.add_header ('Referer',referer)
			
		if __DEBUG__:
			print "sent headers:" + str(req.headers)           
#		response = urllib2.urlopen(url=req,=180,data=postData)
		response = cloudflare.ddos_open(url=req,timeout=180,data=postData)

		if __DEBUG__:
			print "received headers:" + str(response.info());
		
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO.StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			data = f.read()
			#print "received gzip len " + str(len(data))
		   
		else:
			data = response.read()

		if data:
			data = data.replace("\n","").replace("\t","").replace("\r","")   
					 
		try:
			#print sys.modules["__main__"].cookiejar
			sys.modules["__main__"].cookiejar.save()
			
		except Exception,e:
			print e	   
		
		if __DEBUG__:
			print "recieved data:" + str(data)
					   
		response.close()
		
		try:
			if timeout > 999999:
				f = open(cachePath, 'wb')
				f.write(data)
				f.close()
			if __DEBUG__:
				print data
			return data
		except:
			return data
	
def getData(url, timeout=__cachePeriod__, name='', postData=None,referer=__REFERER__):
		for i in range(3):
		  #print "getData: Attempt " + str(i)
		  try:
			return getData_attempt(url, timeout, name, postData,referer)
		  except urllib2.URLError, e:
			print e
			if (i == 2):
			  raise e

def getFinalVideoUrl(series_id,season_id,episode_id,referer,silent=False,m_quality=None):
	CHECK_LOGIN()
	if m_quality is not None and m_quality != 'choose':
		max_quality = m_quality
	else:
		max_quality = int(__settings__.getSetting("max_quality"))
	for i in range(10):
		error = ''
		tok = getData(url=DOMAIN+"/ajax/watch",timeout=1,postData="preWatch=true&SID="+series_id+"&season="+season_id+"&ep="+episode_id,referer=referer)
		try:
			page = getData(url=DOMAIN+"/ajax/watch",timeout=1,postData="watch=true&token="+tok+"&serie="+series_id+"&season="+season_id+"&episode="+episode_id,referer=referer)
			prms=json.loads(page)
			if prms.has_key("error"):
				dp = xbmcgui.DialogProgress()
				dp.create("Sdarot", "אנא המתן 30 שניות", ' ', ' ')
				dp.update(0)
				for s in range(30,-1,-1):
					time.sleep(1)
					dp.update(int((30-s)/30.0 * 100), "אנא המתן 30 שניות", 'עוד {0} שניות'.format(s), '')
					if dp.iscanceled(): 
						dp.close()
						return None,None
				page = getData(url=DOMAIN+"/ajax/watch",timeout=1,postData="watch=true&token="+tok+"&serie="+series_id+"&season="+season_id+"&episode="+episode_id,referer=referer)
		except Exception as e:
			pass
		
		token = None
		
		try:
			prms=json.loads(page)
			if prms.has_key("error"):
				error = str(prms["error"].encode("utf-8"))
				if len(error) > 0 :
					time.sleep(5)
					continue
			
			vid_url = str(prms["url"])
			
			quality = 0
			watch = prms["watch"]
			qualities = []
			for k, v in watch.iteritems():
				qualities.append(k)
				k = int(k)
				if k > quality and k <= max_quality:
					quality = k
					token = v
			if m_quality == 'choose':
				return qualities
			
			VID = str(prms["VID"])
			vid_time = str(prms["time"])
			break
		
		except Exception as e:
			error = e
			time.sleep(5)

	if error <> '':
		xbmc.log('error:'+str(error), 3)
		if not silent:
			xbmcgui.Dialog().ok('Error occurred',str(error))
		return None,None
		
	if not token:
		if not silent:
			xbmcgui.Dialog().ok('Error occurred',"התוסף לא הצליח לקבל אישור לצפייה, אנא נסה מאוחר יותר")
		return None,None
	finalUrl = "http://" + vid_url + "/watch/" + str(quality) + "/" + VID + '.mp4?token=' + token + '&time=' + vid_time
	
	if __settings__.getSetting("use_proxy") == "true":
		finalUrl = "http://127.0.0.1:{0}/?url={1}".format(PROXY_PORT, urllib.quote(finalUrl))

	return "{0}|Referer={1}&User-Agent={2}".format(finalUrl, urllib.quote(referer), __USERAGENT__), VID
	#return finalUrl, VID

def getImage(imageURL, siteName):
		imageName = getImageName(imageURL)
		cacheDir = xbmc.translatePath(os.path.join(__PLUGIN_PATH__, 'cache', 'images', siteName))
		cachePath = xbmc.translatePath(os.path.join(cacheDir, imageName))
		if not os.path.exists(cachePath):
			## fetch the image and store it in the cache path
			if not os.path.exists(cacheDir):
				os.makedirs(cacheDir)
			urllib.urlretrieve(imageURL, cachePath)
		return cachePath
		
def getImageName(imageURL):
		idx = int(imageURL.rfind("/")) + 1
		return imageURL[idx:]

def UnEscapeXML(str):
	return str.replace('&amp;', '&').replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&#039;", "'")
