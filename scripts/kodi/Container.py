class Container:
	def __init__(self, plugin):
		self.plugin = plugin
		self.view = None
		self.window = None
		
	def Update(self, url):
		print 'Updating container with {}'.format(url)
		print self.window.properties
	
	def PluginName(self):
		return self.plugin.name
		
	def ViewMode(self):
		print 'Container viewmode'
		return self.view
		
	def SetViewMode(self, mode):
		self.view = mode