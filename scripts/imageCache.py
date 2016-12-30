import os, urllib2, traceback, time, sys, tempfile, logging
logger = logging.getLogger('TVMLServer')
import kodi_utils

class imageCache:
	
	def __init__(self, limit=100):
		"""limit: number of cache slots to hold. default=100"""
		self.cache = {}
		self.size = 0
		self.limit = limit
		self.dir = tempfile.gettempdir()
			
			
	def add(self, url):
		id = kodi_utils.b64encode(url)
		self.cache[id] = url
		return id
		
			
	def get(self, id):
		return self._download(id)
			
	def _download(self, id):
		try:
			url = self.cache[id]
			if os.path.isfile(os.path.join(self.dir, id)): #if already downloaded
				logger.debug('cached {}'.format(url))
				return os.path.join(self.dir, id)						
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
		
			with open(os.path.join(self.dir, id),'wb') as output:
				output.write(link)
			#urllib.urlretrieve(url, os.path.join(self.dir, name))
			if os.path.isfile(os.path.join(self.dir, id)):
				logger.debug('downloaded {}'.format(url))
				return os.path.join(self.dir, id)
			logger.warning('Failed to download {}'.format(url))
			return None
		except:
			logger.exception('Failed to download image')
			return None