import xml.etree.ElementTree as ET
import os, sys
import importlib
import bridge
from base64 import b64encode
import Plugin

sys.path.append(os.path.join('scripts', 'kodi'))

class KodiPlugin:
	def __init__(self, dir):
		self.dir = dir
		tree = ET.parse(os.path.join(dir, 'addon.xml'))
		for e in tree.iter('addon'):
			self.name = e.attrib['name']
			self.id = e.attrib['id']
		for e2 in tree.iter('extension'):
			if e2.attrib['point'] == 'xbmc.python.pluginsource':
				self.script = e2.attrib['library']
		self.icon = os.path.join(self.dir, 'icon.png')
		self.module = self.script[:-3]
		self.menuurl = '/menu/{}'.format(b64encode(self.name))
		
	def settings(self, bridge, url):
		import xbmc
		xbmc.bridge = bridge
		import xbmcaddon
		xbmcaddon.Addon(self.id).openSettings()
			
	
	def run(self, bridge, url):
		import xbmc
		xbmc.bridge = bridge
		xbmc.currentPlugin = self
		import Container
		xbmc.Container = Container.Container(self)
		if type(url) is not str:
			raise Exception('Kodi plugin only accepts one string argument')
		sys.path.append(os.path.join(os.getcwd(), self.dir))
		fp = open(os.path.join(os.getcwd(), self.dir, self.script), 'rb')
		old_sys_argv = sys.argv
		sys.argv = [os.path.join('file://{}'.format(self.id),self.script), '1', url]
		print 'Calling plugin {} with {}'.format(self.name, sys.argv)
		import xbmcplugin
		import imp
		import urlparse
		xbmcplugin.items = []
		imp.load_module(self.module, fp, os.path.join(os.getcwd(), self.dir), ('.py', 'rb', imp.PY_SOURCE))
		fp.close()
		sys.path.remove(os.path.join(os.getcwd(), self.dir))
		sys.argv = old_sys_argv
		items = xbmcplugin.items
		print 'Plugin {} ended with: {}'.format(self.name, items)
		ans = []
		items = xbmcplugin.items
		from Plugin import Item
		if len(items) == 1 and hasattr(items[0], 'path'):
			return items
		for item in items:
			#url, title, subtitle=None, icon=None, details=None, menuurl='', info={})
			i = Item(url=item['url'], title=item['listitem'].label, subtitle=item['listitem'].getProperty('subtitle'), icon=item['listitem'].thumbnailImage if item['listitem'].thumbnailImage != 'DefaultFolder.png' else '', details=item['listitem'].getProperty('details'),info=item['listitem'].infos)
			infos = item['listitem'].infos
			if 'poster' in infos:
				i.icon = infos['poster']
			if 'plot' in infos:
				i.details = infos['plot']
			if 'year' in infos:
				i.subtitle = infos['year']
			ans.append(i)
		return ans