import importlib

class bridge:
		def __init__(self, app):
			self.app = importlib.import_module(app)
		
		def inputdialog(self, title):
			return self.app.message({'type':'inputdialog', 'title':title, 'description':'blah blah blah'})
			
		def progressdialog(self, heading, line1='', line2='', line3=''):
			return self.app.message({'type':'progressdialog', 'title':heading, 'line1':line1, 'line2':line2, 'line3':line3})
			
		def updateprogressdialog(self, percent, line1='', line2='', line3=''):
			print 'updating progress with {}, {}, {}, {}'.format(percent, line1, line2, line3)
			return self.app.message({'type': 'updateprogress', 'percent':percent, 'line1':line1, 'line2':line2, 'line3':line3})
		
		def isprogresscanceled(self):
			return self.app.message({'type':'isprogresscanceled'}) in ['true', 'True', True]
		
		def closeprogress(self):
			return self.app.message({'type':'closeprogress'})
			
		def selectdialog(self, title, list_):
			return self.app.message({'type':'selectdialog', 'title':title, 'list':list_})
			
		def play(self, url):
			print 'Playing {}'.format(url)
			return self.app.message({'type':'play', 'url':url})
		
		def isplaying(self, ):
			return self.app.message({'type':'isplaying'}) in ['true', 'True', True]