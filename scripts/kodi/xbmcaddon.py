# coding: utf-8
"""
A class to access addon properties
"""

__author__ = 'Team Kodi <http://kodi.tv>'
__credits__ = 'Team Kodi'
__date__ = 'Fri May 01 16:22:07 BST 2015'
__platform__ = 'ALL'
__version__ = '2.20.0'
import os, sys, re, json, time
import codecs
import xml.etree.ElementTree as ET
import xbmc
from collections import OrderedDict
from base64 import b64encode, b64decode

ADDON_CACHE = {}

class Addon(object):
	"""
	Addon(id=None)

	Creates a new Addon class.

	:param id: string - id of the addon (autodetected in XBMC Eden)

	Example::

		self.Addon = xbmcaddon.Addon(id='script.recentlyadded')
	"""
	def __init__(self, id=None):
		"""Creates a new Addon class.

		:param id: string - id of the addon (autodetected in XBMC Eden)

		Example::

			self.Addon = xbmcaddon.Addon(id='script.recentlyadded')
		"""
		global ADDON_CACHE
		self.id = id
		self.strings = {}
		strings_po = os.path.join('kodiplugins', self.id, 'resources', 'language', 'English', 'strings.po')
		strings_xml = os.path.join('kodiplugins', self.id, 'resources', 'language', 'English', 'strings.xml')
		if os.path.isfile(strings_po):
			f = codecs.open(strings_po, mode='r', encoding='UTF-8')
			contents = f.read()
			f.close()
			pattern = re.compile('msgctxt "#(\d+)"\s+msgid "(.*)?"\s+msgstr "(.*)?"')
			for match in pattern.finditer(contents) :
				msgctxt = match.group(1)
				msgid   = match.group(2)
				msgstr  = match.group(3)
        
				if (msgstr) :
					self.strings[msgctxt] = msgstr
				else :
					self.strings[msgctxt] = msgid
		elif os.path.isfile(strings_xml):
			tree = ET.parse(strings_xml)
			for e in tree.iter('string'):
				if 'id' in e.attrib:
					id = e.attrib['id']
					value = e.text
					self.strings[id] = value
		
		if self.id in ADDON_CACHE:
			while ADDON_CACHE[self.id] == 'lock':
				time.sleep(0.1)
			self.settings = ADDON_CACHE[self.id]
		else:
			def isvisible(setting):
				visible = setting['visible']
				if visible == 'false':
					return False
				m = re.search('(!*)eq\(([^,]*),([^,]*)\)', visible)
				if m:
					x=m.group(2)
					y=m.group(3)
					neg=m.group(1) == '!'
					if neg:
						return x != y
					else:
						return x == y
				m = re.search('(!*)System.HasAddon\((.*)\)', visible)
				if m:
					neg = m.group(1) == '!'
					if neg:
						return not os.path.isdir(os.path.join('kodiplugins', m.group(2)))
					else:
						return os.path.isdir(os.path.join('kodiplugins', m.group(2)))
			
			self.settings = OrderedDict()
			settings_xml = os.path.join('kodiplugins', self.id, 'resources', 'settings.xml')
			if os.path.isfile(settings_xml):
				tree = ET.parse(settings_xml)
				iter = tree.iter('category')
				if sum(1 for _ in iter) == 0:
					self.settings['General'] = []
					for e in tree.iter('setting'):
						#dismiss invisible settings
						if 'visible' in e.attrib and not isvisible(e.attrib):
							continue
						if 'default' in e.attrib:
							e.attrib['value'] = e.attrib['default']
						self.settings['General'].append(e.attrib)
				else:
					iter = tree.iter('category')
					for cat in iter:
						label = cat.attrib['label']
						self.settings[label] = []
						for e in cat.iter('setting'):
							#dismiss invisible settings
							if 'visible' in e.attrib and not isvisible(e.attrib):
								continue
							if 'default' in e.attrib:
								e.attrib['value'] = e.attrib['default']
							self.settings[label].append(e.attrib)
				ADDON_CACHE[self.id] = 'lock'
				loaded_settings = json.loads(b64decode(xbmc.bridge._message({'type':'loadSettings'}, True)))
				self.settings.update(loaded_settings)
				ADDON_CACHE[self.id] = self.settings
						

	def getLocalizedString(self, id):
		"""Returns an addon's localized 'unicode string'.

		:param id: integer - id# for string you want to localize.

		Example::

			locstr = self.Addon.getLocalizedString(id=6)
		"""
		try:
			return self.strings[str(id)]
		except:
			return id

	def getSetting(self, id):
		"""Returns the value of a setting as a unicode string.

		:param id: string - id of the setting that the module needs to access.

		Example::

			apikey = self.Addon.getSetting('apikey')
		"""
		for cat in self.settings:
			for s in self.settings[cat]:
				if 'id' in s and s['id'] == id:
					return unicode(s['value'])				
		return None

	def setSetting(self, id, value):
		"""Sets a script setting.

		:param id: string - id of the setting that the module needs to access.
		:param value: string or unicode - value of the setting.

		Example::

			self.Settings.setSetting(id='username', value='teamxbmc')
		"""
		for cat in self.settings:
			for s in self.settings[cat]:
				if 'id' in s and s['id'] == id:
					s['value'] = value

	def openSettings(self):
		"""Opens this scripts settings dialog."""
		sections = OrderedDict()
		for cat in self.settings:
			fields = []
			for attrib in self.settings[cat]:
				if 'type' in attrib and attrib['type'] == 'lsep':
					fields.append({'type':'label', 'label':self.getLocalizedString(attrib['label']), 'value':''})
					continue
				if 'value' not in attrib or 'label' not in attrib:
					continue				
				_type = attrib['type']
				if _type == 'select':
					values = attrib['values'].split("|") if 'values' in attrib else [self.getLocalizedString(s) for s in attrib['lvalues'].split("|")]
					fields.append({'id':attrib['id'], 'type':'selection', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value'], 'choices':values})
				elif _type == 'bool':
					fields.append({'id':attrib['id'], 'type':'yesno', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value']})
				elif _type == 'enum':
					values = attrib['values'].split("|") if 'values' in attrib else [self.getLocalizedString(s) for s in attrib['lvalues'].split("|")]
					fields.append({'id':attrib['id'], 'type':'selection', 'label':self.getLocalizedString(attrib['label']), 'value':values[int(attrib['value'])], 'choices':values})
				elif _type == 'text':
					fields.append({'id':attrib['id'], 'type':'textfield', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value'], 'secure':'option' in attrib and 'hidden' in attrib['option']})
				else:
					fields.append({'type':'label', 'label':self.getLocalizedString(attrib['label']), 'value':'Not supported'})
			if not fields:
				continue
			sections[self.getLocalizedString(cat)] = fields
		ans = xbmc.bridge.formdialog('Addon settings', sections=sections)
		xbmc.bridge._message({'type':'saveSettings','addon':self.id, 'settings':ans})
		def getSet(id):
			for cat in self.settings:
				for s in self.settings[cat]:
					if 'id' in s and s['id'] == id:
						return s				
			return None
		
		for id in ans:
			field = getSet(id)
			if field['type'] == 'select':
				val = ans[id]
			elif field['type'] == 'bool':
				val = ans[id] is 'Yes'
			elif field['type'] == 'enum':
				values = field['values'].split("|") if 'values' in field else [self.getLocalizedString(s) for s in field['lvalues'].split("|")]
				print 'geting index of {} from {}'.format(ans[id], values)
				val = values.index(ans[id])
			elif field['type'] == 'text':
				val = ans[id]
			print 'setting {}={}'.format(id, val)
			self.setSetting(id, val)

	def getAddonInfo(self, id):
		"""Returns the value of an addon property as a string.

		:param id: string - id of the property that the module needs to access.

		.. note::
			Choices are (author, changelog, description, disclaimer, fanart, icon, id, name, path
			profile, stars, summary, type, version)

		Example::

			version = self.Addon.getAddonInfo('version')
		"""
		if id=='path':
			return os.path.join('/kodiplugins', self.id)
		if id=='profile':
			return os.path.join(os.getcwd(), 'kodiplugins', self.id)
		if id=='name':
			return self.id
		return None
