import importlib, time, random, string, sys
from base64 import b64encode, b64decode

def _randomword():
	"""Create a random string of 20 characters"""
	return ''.join(random.choice(string.lowercase) for i in range(20))
   
class bridge:
	"""Bridge class which is created on every client request.
	It is passed to the plugin run method and used to communicate between the plugin and the server.
	For example: pop dialog, request input from user and so on.
	"""
	def __init__(self, app, plugin):
		self.app = importlib.import_module(app)
		self.Thread = getattr(self.app, 'Thread')
		self.thread = None
		
	def _message(self, msg, wait=False, id=None):			
		if not self.thread:
			return None
		if not id:
			id = _randomword()
			msg['id'] = id						
		
		if wait:
			print 'configuring response/{}'.format(id)
			def response(res):
				print 'got response in thread {}'.format(res)
				self.thread.responses.append({'id':id, 'response':res})
				return 'OK', 206
			self.app.add_route(id, response)
		
		print 'adding message: {}'.format(msg)
		self.thread.message(msg)
		if not wait:
			return
		start = time.time()
		while not self.thread.stop and time.time() - start < 3600: #wait for response at most 1 hour. This is meant to limit amount of threads on web server
			for r in self.thread.responses:
				if r['id'] == id:
					print 'received response while waiting: {}'.format(r['response'])
					self.thread.responses.remove(r)
					self.app.remove_route(id)
					return r['response']
			time.sleep(0.1)
		print 'Aborting response wait due to time out'
		try:
			self.app.remove_route(id)
		except:
			pass
		return None
	
	def alertdialog(self, title, description):
		"""Show an alert dialog with title and description. Returns immediately"""
		return self._message({'type':'alertdialog', 'title':title, 'description':description})
		
	def inputdialog(self, title, description='', placeholder='', button='OK', secure=False):
		"""Shows an input dialog to the user with text field. Returns the text the user typed or None if user aborted"""
		s = self._message({'type':'inputdialog', 'title':title, 'description':description, 'placeholder':placeholder, 'button':button, 'secure':secure}, True)
		return b64decode(s) if s else None
		
	def progressdialog(self, heading, text=''):
		id = _randomword()
		self.progress={'title': heading, 'id': id}
		def f():
			self._message({'type':'progressdialog', 'title':heading, 'text':text, 'value':'0', 'id':id}, True, id)
			print 'progress closed'
			self.progress=None
		t = self.Thread(f)
		t.start()
		
	def updateprogressdialog(self, value, text=''):
		if self.progress:
			print 'updating progress with {}, {}'.format(value, text)
			return self._message({'type':'progressdialog', 'title':self.progress['title'], 'text':text, 'value':value, 'id':self.progress['id']}, False, self.progress['id'])
	
	def isprogresscanceled(self):
		return not self.progress
	
	def closeprogress(self):
		return self._message({'type':'closeprogress'})
		
	def selectdialog(self, title, list_):
		return self._message({'type':'selectdialog', 'title':title, 'list':list_}, True)				
		
	def play(self, url, type_='video', title=None, description=None, image=None, subtitle_url=None, stop_completion=None):
		print 'Playing {}'.format(url)
		self.play = url
		def stop(res):
			self.play = None
			print 'detected player stop at time {}'.format(b64decode(res))
			if stop_completion:
				stop_completion(b64decode(res))
			return 'OK', 206
		id = _randomword()
		self.app.add_route(id, stop)
		return self._message({'type':'play', 'url':url, 'stop':'/response/{}'.format(id), 'playtype': type_, 'subtitle':subtitle_url, 'title':title, 'description':description, 'image':image})
	
	def isplaying(self):
		return self.play is not None