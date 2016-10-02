import importlib, time, sys, json, utils
import multiprocessing
try:
	import setproctitle
except:
	pass

def play_stop(b, _id, stop_completion):
	res = None
	if 'setproctitle' in sys.modules:
		setproctitle.setproctitle('python TVMLServer (play wait {})'.format(_id))
	while not b.thread.stop:
		try:
			r = b.thread.responses.get(False)
			print 'found response for {}'.format(r['id'])
			if r['id'] == _id:
				print 'received response to {}'.format(_id)
				res = r['response']
				break
			else:
				b.thread.responses.put(r)					
		except:
			time.sleep(1)
	b.play = None
	print 'detected player stop at time {}'.format(utils.b64decode(res))
	if stop_completion:
		stop_completion(utils.b64decode(res))
		
def progress_stop(b, _id):
	if 'setproctitle' in sys.modules:
		setproctitle.setproctitle('python TVMLServer (progress dialog {})'.format(_id))
	while b.progress and not b.thread.stop:
		try:
			r = b.thread.responses.get(False)
			print 'found response for {}'.format(r['id'])
			if r['id'] == _id:
				print 'received progress close'
				print 'received response to {}'.format(_id)
				print 'progress closed'
				b.progress=None
			else:
				b.thread.responses.put(r)					
		except:			
			time.sleep(1)
   
class bridge:
	"""Bridge class which is created on every client request.
	It is passed to the plugin run method and used to communicate between the plugin and the server.
	For example: pop dialog, request input from user and so on.
	"""
	def __init__(self):
		self.thread = multiprocessing.current_process()
		
	def _message(self, msg, wait=False, _id=None):			
		if not self.thread:
			return None
		if not _id:
			_id = utils.randomword()
			msg['id'] = '{}/{}'.format(self.thread.id, _id)						
		
		print 'adding message: {}'.format(msg)
		self.thread.message(msg)
		if not wait:
			return
		start = time.time()		
		while not self.thread.stop and time.time() - start < 3600: #wait for response at most 1 hour. This is meant to limit amount of threads on web server			
			try:
				r = self.thread.responses.get(False)
				print 'found response for {}'.format(r['id'])
				if r['id'] == _id:
					print 'received response to {}'.format(_id)
					return r['response']
				else:
					self.thread.responses.put(r)
			except:
				time.sleep(0.1)
		if self.thread.stop:
			print 'finished waiting for response {} due to thread stop'.format(_id)
		else:
			print 'Aborting response wait due to time out'
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
		_id = utils.randomword()
		self.progress={'title': heading, 'id': _id}					
		multiprocessing.Process(target=progress_stop, args=(self, _id)).start()
		self._message({'type':'progressdialog', 'title':heading, 'text':text, 'value':'0', 'id':'{}/{}'.format(self.thread.id, _id)}, False, _id)
		
	def updateprogressdialog(self, value, text=''):
		"""Updates the progress dialog"""
		if self.progress:
			print 'updating progress with {}, {}'.format(value, text)
			return self._message({'type':'progressdialog', 'title':self.progress['title'], 'text':text, 'value':value, 'id':'{}/{}'.format(self.thread.id, self.progress['id'])}, False, self.progress['id'])
	
	def isprogresscanceled(self):
		"""Returns whether the progress dialog is still showing or canceled by user"""
		print 'isprogresscanceled {}'.format(not self.progress)
		return not self.progress
	
	def closeprogress(self):
		"""Closes the progress dialog"""
		self.progress = None
		return self._message({'type':'closeprogress'})
		
	def selectdialog(self, title, text='', list_=[]):
		"""Shows a selection dialog"""
		ans = self._message({'type':'selectdialog', 'title':title, 'text':text, 'list':list_}, True)				
		time.sleep(1)
		return ans
		
	def play(self, url, type_='video', title=None, description=None, image=None, subtitle_url=None, stop_completion=None):
		"""Plays a url"""
		print 'Playing {}'.format(url)
		self.play = url
		_id = utils.randomword()		
		multiprocessing.Process(target=play_stop, args=(self, _id, stop_completion)).start()	
		self._message({'type':'play', 'url':url, 'stop':'/response/{}/{}'.format(self.thread.id, _id), 'playtype': type_, 'subtitle':subtitle_url, 'title':title, 'description':description, 'image':image})
		return 
	
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
