import xml.etree.ElementTree as ET
import os, sys, json
import importlib
from xml.sax.saxutils import escape
import bridge

class Item:
	def __init__(self, url, title, subtitle=None, icon=None, details=None, menuurl='', info={}, context={}):
		self.url = url
		self.title = title #'[COLOR green] >>	 Move to next page[/COLOR]'
		self.subtitle = escape(subtitle) if subtitle else None
		self.icon = icon
		self.details = escape(details) if details else None
		self.menuurl = menuurl
		self.info = info
		self.context = context
	def __repr__(self):
		return json.dumps({"url":self.url, "title":self.title, "subtitle":self.subtitle, "icon":self.icon, "details":self.details, "menuurl":self.menuurl, "info":self.info, "context":self.context})


class Plugin:
	def __init__(self, dir):
		self.id = dir.split(os.path.sep)[1]			
		self.dir = dir
		tree = ET.parse(os.path.join(dir, 'addon.xml'))
		for e in tree.iter('addon'):
			self.name = e.attrib['name']
			self.script = e.attrib['script']
			self.icon = os.path.join(self.dir, e.attrib['icon'])			
		sys.path.append(os.path.join(os.getcwd(), self.dir))
		self.module = self.script[:-3] #remove the .py
		self.menuurl = ''
		
	
	def run(self, bridge, url):
		"""Run the plugin on a url argument and expect a list of Item

		:param url: a url if the last item that was selected. Initially it will be an empty string
	   
		Example::

		plugin.run('')"""
		m = importlib.import_module(self.module)
		return m.main(bridge, url)	
		
	def __repr__(self):
		return str({'name':self.name, 'dir':self.dir, 'script':self.script, 'icon':self.icon, 'module':self.module})
