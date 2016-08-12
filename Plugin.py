import xml.etree.ElementTree as ET
import os, sys
import importlib

class Item:
	def __init__(self, url, title, subtitle=None, icon=None, details=None, info={}):
		self.url = url
		self.title = striptags(title) #'[COLOR green] >>  Move to next page[/COLOR]'
		self.subtitle = subtitle
		self.icon = icon
		self.details = details
		self.info = info
	def __repr__(self):
		return str({'url':self.url, 'title':self.title, 'subtitle':self.subtitle, 'icon':self.icon, 'details':self.details, 'info':self.info})
	
def striptags(s):
	if s.rfind('[')>0:
		return s[s.index(']')+1:s.rfind('[')].replace('<','').replace('>','').strip()
	else:
		return s


class Plugin:
	def __init__(self, bridge, dir):
		self.bridge = importlib.import_module(bridge)
		self.dir = dir
		tree = ET.parse(os.path.join(dir, 'addon.xml'))
		for e in tree.iter('addon'):
			self.name = e.attrib['name']
			self.script = e.attrib['script']
			self.icon = os.path.join(self.dir, e.attrib['icon'])			
		sys.path.append(os.path.join(os.getcwd(), self.dir))
		self.module = importlib.import_module(self.script[:-3]) #remove the .py

	"""Run the plugin on a set of arguments and expect a list of Item

    :param *args: a list of arguments to pass to the plugin main method
       
    Example::

        plugin.run('1', 'hello world')
    """
	def run(self, *args):
		return self.module.main(self.bridge, *args)	
		
	def __repr__(self):
		return str({'name':self.name, 'dir':self.dir, 'script':self.script, 'icon':self.icon, 'module':self.module})
