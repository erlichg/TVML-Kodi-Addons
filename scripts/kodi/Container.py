import logging
logger = logging.getLogger('TVMLServer')

class Container:
	def __init__(self, plugin):
		self.plugin = plugin
		self.view = None
		
	def Update(self, url):
		logger.debug('Updating container with {}'.format(url))
	
	def PluginName(self):
		return self.plugin.name
		
	def ViewMode(self):
		logger.debug('Container viewmode')
		return self.view
		
	def SetViewMode(self, mode):
		self.view = mode