# coding: utf-8
"""
A class to access addon properties
"""

__author__ = 'Team Kodi <http://kodi.tv>'
__credits__ = 'Team Kodi'
__date__ = 'Fri May 01 16:22:07 BST 2015'
__platform__ = 'ALL'
__version__ = '2.20.0'
import os, sys, re, json, time, logging
logger = logging.getLogger('TVMLServer')
import codecs
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import xbmc, kodi_utils
from KodiPlugin import KodiPlugin
from collections import OrderedDict

ADDON_CACHE = {}

class Addon(object):

    def __new__(cls, id=None, settings=None):
        if not id:
            import traceback
            stack = traceback.extract_stack()[:-1]
            print 'searching for id in {}'.format(stack)
            for s in stack:
                m = re.search(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', '([^{}]+)'.format(os.path.sep)).encode('string-escape'), s[0])
                if m:
                    print 'Found id {}'.format(m.group(1))
                    id = m.group(1)
                    break
            if not id:
                raise Exception('Could not find addon ID automatically')
        global ADDON_CACHE
        if id in ADDON_CACHE:
            return ADDON_CACHE[id]
        else:
            ans = super(Addon, cls).__new__(cls, id, settings)
            ADDON_CACHE[id] = ans
            return ans

    def __init__(self, id=None, settings=None):
        """Creates a new Addon class.

        :param id: string - id of the addon (autodetected in XBMC Eden)

        Example::

            self.Addon = xbmcaddon.Addon(id='script.recentlyadded')
        """
        try:
            if self.settings and self.strings_en:
                return
        except:
            logger.debug('Creating new instance of addon {}'.format(id))
        if not id:
            import traceback
            stack = traceback.extract_stack()[:-1]
            print 'searching for id in {}'.format(stack)
            for s in stack:
                m = re.search(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', '([^{}]+)'.format(os.path.sep)).encode('string-escape'), s[0])
                if m:
                    print 'Found id {}'.format(m.group(1))
                    id = m.group(1)
                    break
            if not id:
                raise Exception('Could not find addon ID automatically')

        self.plugin = KodiPlugin(id)
        self.strings = {}
        self.strings_en = {}
        try:
            strings_po = os.path.join(self.getAddonInfo('path'), 'resources', 'language', xbmc.LANGUAGE, 'strings.po')
            if not os.path.isfile(strings_po):
                strings_xml = os.path.join(self.getAddonInfo('path'), 'resources', 'language', xbmc.LANGUAGE, 'strings.xml')
            strings_po_en = os.path.join(self.getAddonInfo('path'), 'resources', 'language', 'English', 'strings.po')
            if not os.path.isfile(strings_po_en):
                strings_xml_en = os.path.join(self.getAddonInfo('path'), 'resources', 'language', 'English', 'strings.xml')
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
                f = codecs.open(strings_xml, mode='r', encoding='UTF-8')
                contents = f.read().replace('&', '&amp;')
                f.close()
                tree = ET.fromstring(contents)
                for e in tree.iter('string'):
                    if 'id' in e.attrib:
                        id = e.attrib['id']
                        value = e.text
                        self.strings[id] = value
            if os.path.isfile(strings_po_en):
                f = codecs.open(strings_po_en, mode='r', encoding='UTF-8')
                contents = f.read()
                f.close()
                pattern = re.compile('msgctxt "#(\d+)"\s+msgid "(.*)?"\s+msgstr "(.*)?"')
                for match in pattern.finditer(contents) :
                    msgctxt = match.group(1)
                    msgid   = match.group(2)
                    msgstr  = match.group(3)

                    if (msgstr) :
                        self.strings_en[msgctxt] = msgstr
                    else :
                        self.strings_en[msgctxt] = msgid
            elif os.path.isfile(strings_xml_en):
                f = codecs.open(strings_xml_en, mode='r', encoding='UTF-8')
                contents = f.read().replace('&', '&amp;')
                f.close()
                tree = ET.fromstring(contents)
                for e in tree.iter('string'):
                    if 'id' in e.attrib:
                        id = e.attrib['id']
                        value = e.text
                        self.strings_en[id] = value
        except:
            logger.exception('Failed to read addon strings')

        try:
            self.settings = OrderedDict()
            settings_xml = os.path.join(self.getAddonInfo('path'), 'resources', 'settings.xml')
            if os.path.isfile(settings_xml):
                f = codecs.open(settings_xml, mode='r', encoding='UTF-8')
                contents = f.read().replace('&', '&amp;')
                f.close()
                tree = ET.fromstring(contents)
                iter = tree.iter('category')
                if sum(1 for _ in iter) == 0:
                    self.settings['General'] = []
                    for e in tree.iter('setting'):
                        if 'default' in e.attrib:
                            e.attrib['value'] = e.attrib['default']
                        if not 'value' in e.attrib:
                            e.attrib['value'] = ''
                        self.settings['General'].append(e.attrib)
                else:
                    iter = tree.iter('category')
                    for cat in iter:
                        label = cat.attrib['label']
                        self.settings[label] = []
                        for e in cat.iter('setting'):
                            if 'default' in e.attrib:
                                e.attrib['value'] = e.attrib['default']
                            if not 'value' in e.attrib:
                                e.attrib['value'] = ''
                            self.settings[label].append(e.attrib)
                if settings:
                    self.settings.update(settings)
        except:
            logger.exception('Failed to read addon settings')
            self.settings = OrderedDict()

    def getLocalizedString(self, id):
        """Returns an addon's localized 'unicode string'.

        :param id: integer - id# for string you want to localize.

        Example::

            locstr = self.Addon.getLocalizedString(id=6)
        """
        try:
            return self.strings[str(id)]
        except:
            try:
                return self.strings_en[str(id)]
            except:
                return id

    def getSetting(self, _id):
        """Returns the value of a setting as a unicode string.

        :param id: string - id of the setting that the module needs to access.

        Example::

            apikey = self.Addon.getSetting('apikey')
        """

        for cat in self.settings:
            for s in self.settings[cat]:
                if 'id' in s and s['id'] == _id:
                    ans = unicode(s['value'])
                    #logger.debug('getSetting {}={}'.format(id, ans))
                    return ans
                elif 'id' not in s and 'label' in s and 'type' in s and (s['label']+s['type']) == _id:
                    ans = unicode(s['value'])
                    # logger.debug('getSetting {}={}'.format(id, ans))
                    return ans
        #logger.debug('getSetting {}='.format(id))
        return ''

    def setSetting(self, _id, value):
        """Sets a script setting.

        :param id: string - id of the setting that the module needs to access.
        :param value: string or unicode - value of the setting.

        Example::

            self.Settings.setSetting(id='username', value='teamxbmc')
        """
        logger.debug('setSetting {}={}'.format(_id, value))
        for cat in self.settings:
            for s in self.settings[cat]:
                if 'id' in s and s['id'] == _id:
                    s['value'] = value
                    return
                elif not 'id' in s and 'label' in s and (s['label'] + s['type']) == _id:
                    s['value'] = value
                    return
        #if we got here this means key does not exist
        for cat in self.settings:
            self.settings[cat].append({'id':_id, 'value':value})
            break

    def openSettings(self):
        """Opens this scripts settings dialog."""
        if not self.settings:
            xbmc.bridge.alertdialog('No settings', 'This addon does not have any settings available for view or modification')
            return
        sections = OrderedDict()
        def isvisible(visible, i, category):
            if visible == 'false':
                return False
            if visible == 'true':
                return True
            if '|' in visible:
                for v in visible.split('|'):
                    if isvisible(v, i, category):
                        return True
                return False
            if '+' in visible:
                for v in visible.split('+'):
                    if not isvisible(v, i, category):
                        return False
                return True
            m = re.search('(!*)(eq|gt|lt)\(([^,]*),([^,]*)\)', visible)
            if m:
                x=m.group(3)
                y=m.group(4)
                try:
                    int(x)
                    x = category[i+int(x)]['value']
                except:
                    pass
                try:
                    int(y)
                    y = category[i+int(y)]['value']
                except:
                    pass
                sign = m.group(2)
                if sign == 'eq':
                    ans = x == y
                elif sign == 'gt':
                    ans = x > y
                elif sign == 'lt':
                    ans = x < y
                else:
                    logger.error('Unknown operator in visible setting {}'.format(category[i]))
                neg=m.group(1) == '!'
                if neg:
                    return not ans
                else:
                    return ans
            m = re.search('(!*)System.HasAddon\((.*)\)', visible)
            if m:
                neg = m.group(1) == '!'
                if neg:
                    return not os.path.isdir(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', m.group(2)))
                else:
                    return os.path.isdir(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', m.group(2)))
            return True
        for cat in self.settings:
            fields = []
            for (i,attrib) in enumerate(self.settings[cat]):
                if 'visible' in attrib and not isvisible(attrib['visible'], i, self.settings[cat]):
                    continue
                if 'label' not in attrib:
                    continue
                if 'id' not in attrib:
                    attrib['id'] = (attrib['label']+attrib['type'])
                _type = attrib['type']
                if _type == 'select' or _type == 'labelenum':
                    values = attrib['values'].split("|") if 'values' in attrib else [self.getLocalizedString(s) for s in attrib['lvalues'].split("|")]
                    fields.append({'id':attrib['id'], 'type':'selection', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value'], 'choices':values})
                elif _type == 'bool':
                    fields.append({'id':attrib['id'], 'type':'yesno', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value']})
                elif _type == 'enum':
                    values = attrib['values'].split("|") if 'values' in attrib else [self.getLocalizedString(s) for s in attrib['lvalues'].split("|")]
                    try:
                        val = values[int(attrib['value'])]
                    except:
                        val =  values.index(attrib['value'])
                    fields.append({'id':attrib['id'], 'type':'selection', 'label':self.getLocalizedString(attrib['label']), 'value':val, 'choices':values})
                elif _type == 'text':
                    fields.append({'id':attrib['id'], 'type':'textfield', 'label':self.getLocalizedString(attrib['label']), 'value':attrib['value'], 'secure':'option' in attrib and 'hidden' in attrib['option']})
                elif _type == 'action':
                    fields.append({'id':attrib['id'], 'type':'action', 'label':self.getLocalizedString(attrib['label']), 'action':attrib['action'], 'value':attrib['value'] if 'value' in attrib else ''})
                elif _type == 'lsep' or _type == 'sep':
                    fields.append({'type':'sep', 'label':self.getLocalizedString(attrib['label'])})
                elif _type == 'ipaddress':
                    fields.append({'id': attrib['id'], 'type': 'ipaddress', 'label': self.getLocalizedString(attrib['label']), 'value': attrib['value'], 'secure': 'option' in attrib and 'hidden' in attrib['option']})
                elif _type == 'number':
                    fields.append({'id': attrib['id'], 'type': 'number', 'label': self.getLocalizedString(attrib['label']), 'value': attrib['value'], 'secure': 'option' in attrib and 'hidden' in attrib['option']})
                elif _type == 'slider':
                    fields.append({'id': attrib['id'], 'type': 'slider', 'label': self.getLocalizedString(attrib['label']), 'value': attrib['value'], 'secure': 'option' in attrib and 'hidden' in attrib['option']})
                else:
                    fields.append({'type':'label', 'label':self.getLocalizedString(attrib['label']), 'value':'Not supported'})
            if not fields:
                continue
            sections[self.getLocalizedString(cat)] = fields
        ans = xbmc.bridge.formdialog('Addon settings', sections=sections, cont=True)
        def getSet(_id):
            for cat in self.settings:
                for s in self.settings[cat]:
                    if 'id' in s and s['id'] == _id:
                        return s
                    elif not 'id' in s and 'label' in s and (s['label'] + s['type']) == _id:
                        return s
            return None

        for id in ans:
            field = getSet(id)
            if field['type'] in ['select', 'labelenum']:
                val = ans[id]
            elif field['type'] == 'bool':
                val = 'true' if ans[id] == 'Yes' else 'false'
            elif field['type'] == 'enum':
                values = field['values'].split("|") if 'values' in field else [self.getLocalizedString(s) for s in field['lvalues'].split("|")]
                val = values.index(ans[id])
            elif field['type'] in ['text', 'ipaddress', 'number', 'slider']:
                val = ans[id]
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
        if id=='path': #addon orig path
            ans = os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', self.plugin.id)
            if not os.path.exists(ans):
                os.makedirs(ans)
            return ans
        if id=='profile': #user data dir
            ans = os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'userdata', self.plugin.id)
            if not os.path.exists(ans):
                os.makedirs(ans)
            return ans
        if id=='name':
            return self.plugin.name
        if id=='version':
            return self.plugin.version
        if id=='id':
            return self.plugin.id
        return None
