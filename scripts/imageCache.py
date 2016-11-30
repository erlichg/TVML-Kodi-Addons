import os, urllib2, traceback, time, sys
import kodi_utils

class imageCache:
	
	class fileCache:
		def __init__(self, file):
			self.file = file			
			stat = os.stat(file)
			self.size = stat.st_size
			self.time = time.time()
		def __str__(self):
			return 'file={}, size={}, time={}'.format(self.file, self.size, self.time)
			
	def __init__(self, dir, limit=0):
		if not os.path.exists(dir):
			os.mkdir(dir)
		if not os.path.isdir(dir):
			raise Exception('dir must be a directory')
		self.cache = {}
		self.size = 0
		self.dir = dir
		self.limit = limit
		for f in os.listdir(self.dir):
			try:
				self.add(kodi_utils.b64decode(f), os.path.join(self.dir, f))
			except:
				continue
			
			
	def add(self, url, f):
		try:	
			self.cache[url] = self.fileCache(f)
			self.size += self.cache[url].size
			while self.limit != 0 and self.size > self.limit:
				to_remove = None			
				for key in self.cache:
					if not to_remove or self.cache[key].time < self.cache[to_remove].time:
						to_remove = key
				print 'removing {}'.format(self.cache[to_remove])
				os.remove(self.cache[to_remove].file)
				self.size -= self.cache[to_remove].size
				print 'size after removal {}'.format(self.size)
				del self.cache[to_remove]
		except:
			del self.cache[url]
			
	def get(self, url):
		if url in self.cache:
			return '/{}'.format(self.cache[url].file)
		elif self.download(url):
			return '/{}'.format(self.cache[url].file)
		else:
			return url
			
	def download(self, url):
		try:
			print 'downloading {}'.format(url)
			if url in self.cache:
				return True
			name = kodi_utils.b64encode(url)
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
		
			with open(os.path.join(self.dir, name),'wb') as output:
				output.write(link)
			#urllib.urlretrieve(url, os.path.join(self.dir, name))
			if os.path.isfile(os.path.join(self.dir, name)):
				print 'downloaded {}'.format(url)
				self.add(url, os.path.join(self.dir, name))
				return True
			print 'Failed to download {}'.format(url)
			return False
		except:
			traceback.print_exc(file=sys.stdout)
			return False