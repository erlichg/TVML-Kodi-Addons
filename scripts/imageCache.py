import os, urllib2, traceback, time, sys, tempfile, logging
logger = logging.getLogger('TVMLServer')
import kodi_utils



def get(encoded_url, dir = tempfile.gettempdir()):		
	try:			
		url = kodi_utils.b64decode(encoded_url)
		if os.path.isfile(os.path.join(dir, encoded_url)): #if already downloaded
			logger.debug('cached {}'.format(url))
			return os.path.join(dir, encoded_url)						
		logger.debug('downloading {}'.format(url))
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36')
		req.add_header('Accept-encoding', 'gzip')
		response = urllib2.urlopen(req,timeout=100)
		if response.info().get('Content-Encoding') == 'gzip':
			buf = StringIO( response.read())
			f = gzip.GzipFile(fileobj=buf)
			link = f.read()
		else:
			link = response.read()
		response.close()
	
		with open(os.path.join(dir, encoded_url),'wb') as output:
			output.write(link)
		#urllib.urlretrieve(url, os.path.join(self.dir, name))
		if os.path.isfile(os.path.join(dir, encoded_url)):
			logger.debug('downloaded {}'.format(url))
			return os.path.join(dir, encoded_url)
		logger.warning('Failed to download {}'.format(url))
		return None
	except:
		logger.exception('Failed to download image')
		return None