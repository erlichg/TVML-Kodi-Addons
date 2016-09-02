import importlib, time, sys, json, utils


	
   
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
			id = utils.randomword()
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
			print 'waiting for message to {}'.format(id)
			for r in self.thread.responses:
				if r['id'] == id:
					print 'received response while waiting: {}'.format(r['response'])
					self.thread.responses.remove(r)
					self.app.remove_route(id)
					return r['response']
			time.sleep(0.1)
		if self.thread.stop:
			print 'finished waiting for response due to thread stop'
		else:
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
		return utils.b64decode(s) if s else None
		
	def progressdialog(self, heading, text=''):
		"""Shows a progress dialog to the user"""
		id = utils.randomword()
		self.progress={'title': heading, 'id': id}
		def f():
			self._message({'type':'progressdialog', 'title':heading, 'text':text, 'value':'0', 'id':id}, True, id)
			print 'progress closed'
			self.progress=None
		t = self.Thread(f)
		t.start()
		
	def updateprogressdialog(self, value, text=''):
		"""Updates the progress dialog"""
		if self.progress:
			print 'updating progress with {}, {}'.format(value, text)
			return self._message({'type':'progressdialog', 'title':self.progress['title'], 'text':text, 'value':value, 'id':self.progress['id']}, False, self.progress['id'])
	
	def isprogresscanceled(self):
		"""Returns whether the progress dialog is still showing or canceled by user"""
		return not self.progress
	
	def closeprogress(self):
		"""Closes the progress dialog"""
		return self._message({'type':'closeprogress'})
		
	def selectdialog(self, title, list_):
		"""Shows a selection dialog"""
		return self._message({'type':'selectdialog', 'title':title, 'list':list_}, True)				
		
	def play(self, url, type_='video', title=None, description=None, image=None, subtitle_url=None, stop_completion=None):
		"""Plays a url"""
		print 'Playing {}'.format(url)
		self.play = url
		def stop(res):
			self.play = None
			print 'detected player stop at time {}'.format(utils.b64decode(res))
			if stop_completion:
				stop_completion(utils.b64decode(res))
			return 'OK', 206
		id = utils.randomword()
		self.app.add_route(id, stop)
		return self._message({'type':'play', 'url':url, 'stop':'/response/{}'.format(id), 'playtype': type_, 'subtitle':subtitle_url, 'title':title, 'description':description, 'image':image})
	
	def isplaying(self):
		"""Returns whether the player is still showing or has been cancelled"""
		return self.play is not None
		
	def formdialog(self, title, fields=[], sections={}, cont=False):
		"""Show a custom form dialog with custom fields
			A field is an object with a type, a label, a value (initial) and other attributes depending on its type.
			Available types are: textfield, yesno and selection
			textfield:
				displayed as a label. when clicked, user is presented with an input form to modify the field. Additional optional attributes: description, placeholder, button and secure.
			yesno:
				value must be a boolean. displayed as a label with 'Yes' or 'No' depending on the value. Clicking on it changes the value between 'Yes' and 'No'. Has no other attributes.
			selection:
				displayed exactly like yesno, but clicking rotates the field on values from the list. possible values are passed via the 'choices' attribute. Initial value must be one of the choices.
				
			There are 2 ways you can call this function: With a list of fields passed with the fields parameter, or a dict of sections where key is the title, and value is a list of fields
			
			cont is a boolean whether to continue receiving messages after form has been dismissed
			returns a dict with keys as field labels and values as their (modified) value
			"""
		if fields:
			s = self._message({'type':'formdialog', 'title':title, 'sections':{'General':fields}, 'cont':cont}, True)
		elif sections:
			s = self._message({'type':'formdialog', 'title':title, 'sections':sections, 'cont':cont}, True)
		else:
			raise Exception('Must have either fields or sections')
		return json.loads(utils.b64decode(s)) if s else None