import xml.etree.ElementTree as ET
import os, sys, re, json, time, AdvancedHTMLParser
import importlib
import bridge
import kodi_utils
import Plugin
import traceback
import logging

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = '.'

ADDONS_DIR = os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons')


def convert_kodi_tags_to_html_tags(s):
    s = s.replace('[B]', '<b>')
    s = s.replace('[/B]', '</b>')
    s = s.replace('[I]', '<i>')
    s = s.replace('[/I]', '</i>')
    return s

def parse_addon_xml(text, repo=None, dir=None):
    parser = AdvancedHTMLParser.Parser.AdvancedHTMLParser()
    parser.feed(text)
    temp = []
    for a in parser.getElementsByTagName('addon'):
        id = a.attributes['id']
        data = a.attributes
        try:
            meta = a.getElementsByAttr('point', 'xbmc.addon.metadata')[0]
            data.update({t.tagName: t.text for t in meta.children})
            english = a.getElementsByAttr('lang', 'en')
            if english:
                data.update({t.tagName: t.text for t in english})
        except:
            pass
        addon_type = []
        script = ''
        requires = []
        try:
            ext = a.getElementsCustomFilter(lambda x: x.tagName == 'extension')
            for e in ext:
                point = e.attributes['point']
                if point == 'xbmc.addon.metadata':
                    continue
                if point == 'xbmc.gui.skin':
                    addon_type.append('Skin')
                elif point == 'xbmc.webinterface':
                    addon_type.append('Web interface')
                elif point == 'xbmc.addon.repository':
                    addon_type.append('Repository')
                elif point == 'xbmc.service':
                    addon_type.append('Service')
                elif point == 'xbmc.metadata.scraper.albums':
                    addon_type.append('Album information')
                elif point == 'xbmc.metadata.scraper.artists':
                    addon_type.append('Artist information')
                elif point == 'xbmc.metadata.scraper.movies':
                    addon_type.append('Movie information')
                elif point == 'xbmc.metadata.scraper.musicvideos':
                    addon_type.append('Music video information')
                elif point == 'xbmc.metadata.scraper.tvshows':
                    addon_type.append('TV information')
                elif point == 'xbmc.metadata.scraper.library':
                    addon_type.append('Library')
                elif point == 'xbmc.ui.screensaver':
                    addon_type.append('Screensaver')
                elif point == 'xbmc.player.musicviz':
                    addon_type.append('Visualization')
                elif point == 'xbmc.python.pluginsource' or point == 'xbmc.python.script':
                    script = e.attributes['library']
                    provides = e.getElementsCustomFilter(lambda x: x.tagName == 'provides')
                    if provides:
                        text = provides[0].text
                        if 'image' in text:
                            addon_type.append('Picture')
                        if 'audio' in text:
                            addon_type.append('Audio')
                        if 'video' in text:
                            addon_type.append('Video')
                        if 'executable' in text:
                            addon_type.append('Program')
                    imports = a.getElementsCustomFilter(lambda x: x.tagName == 'import')
                    requires = [i.attributes['addon'] for i in imports]
                elif point == 'xbmc.python.weather':
                    addon_type.append('Weather')
                elif point == 'xbmc.subtitle.module':
                    addon_type.append('Subtitles')
                elif point == 'xbmc.python.lyrics':
                    addon_type.append('Lyrics')
                elif point == 'xbmc.python.library':
                    addon_type.append('Other')
                elif point == 'xbmc.python.module':
                    addon_type.append('Other')
                elif point == 'xbmc.addon.video':
                    addon_type.append('Video')
                elif point == 'xbmc.addon.audio':
                    addon_type.append('Audio')
                elif point == 'xbmc.addon.image':
                    addon_type.append('Picture')
                elif point == 'kodi.resource.images':
                    addon_type.append('Other')
                elif point == 'kodi.resource.language':
                    addon_type.append('Other')
                else:
                    addon_type.append('Other')
        except:
            pass
        if not addon_type:
            print 'Failed to determine addon type of {}'.format(id)
        temp.append({'id': id, 'repo': repo, 'dir': dir, 'type': addon_type, 'name': data['name'], 'data': data, 'version': data['version'], 'script': script, 'requires': requires,
                                'icon': '/cache/{}'.format(
                                    kodi_utils.b64encode('{}/{}/icon.png'.format(dir['download'], id))) if dir else None})
    return temp


class KodiPlugin:
    def __init__(self, id):
        self.dir = os.path.join(ADDONS_DIR, id)
        with open(os.path.join(self.dir, 'addon.xml'), 'r') as f:
            data = parse_addon_xml(f.read())[0]
            self.name = data['name']
            self.id = data['id']
            self.version = data['version']
            self.script = data['script']
            self.requires = data['requires']
            self.icon = '/addons/{}/icon.png'.format(self.id)
            self.module = self.script[:-3]
            self.type = data['type']
            self.data = data['data']

    def __repr__(self):
        return json.dumps({'id': self.id, 'name': self.name, 'module': self.module})

    def settings(self, bridge, url, LANGUAGE, settings):

        import xbmc
        xbmc.bridge = bridge
        xbmc.LANGUAGE = LANGUAGE
        import xbmcaddon
        xbmcaddon.Addon(self.id, settings)
        xbmcaddon.Addon(self.id).openSettings()


    def run(self, bridge, url, LANGUAGE, settings):
        logger = logging.getLogger(self.id)
        if url.startswith('http') or url.startswith('https'):
            bridge.play(url, type_='video')
            return
        orig = sys.path
        sys.path.append(self.dir)
        sys.path.append(os.path.join(bundle_dir, 'scripts'))
        sys.path.append(os.path.join(bundle_dir, 'scripts', 'kodi'))

        for r in self.requires:
            if not os.path.exists(os.path.join(ADDONS_DIR, r)):
                logger.error('Addon {} is missing module {}'.format(self.id, r))
                return None

            tree = ET.parse(os.path.join(ADDONS_DIR, r, 'addon.xml'))
            for e2 in tree.iter('extension'):
                if e2.attrib['point'] == 'xbmc.python.module':
                    sys.path.append(os.path.join(ADDONS_DIR, r, e2.attrib['library']))
        print sys.path


        import xbmc

        xbmc.bridge = bridge
        import Container
        xbmc.Container = Container.Container(self)
        xbmc.LANGUAGE = LANGUAGE
        if type(url) is not str:
            raise Exception('Kodi plugin only accepts one string argument')

        try:
            fp = open(os.path.join(bundle_dir, self.dir, self.script), 'rb')
            if '?' in url:
                sys.argv = [url.split('?')[0], '1', '?{}'.format(url.split('?')[1])]
            else:
                sys.argv = [url, '1', '']

            if not sys.argv[0]:
                sys.argv[0] = 'file://{}/'.format(self.id)

            if not sys.argv[0].startswith('file://') and not sys.argv[0].startswith('plugin://'):
                sys.argv[0] = 'file://{}{}'.format(self.id, sys.argv[0])
        # sys.argv = [script, '1', url]
            logger.debug('Calling plugin {} with {}'.format(self.name, sys.argv))
            import xbmcplugin, xbmcaddon
            xbmcaddon.Addon(self.id, settings)
            import imp

    # some patches for internal python funcs
            import urllib

            quote_plus_orig = urllib.quote_plus


            def quote_plus_patch(s, safe=''):
                if type(s) == unicode:
                    s = s.encode('utf-8')
                return quote_plus_orig(s, safe)


            urllib.quote_plus = quote_plus_patch

            import sqlite3

            sqlite3_connect_orig = sqlite3.connect


            def sqlite3_connect_patch(*args, **kwargs):
                logger.debug('sqlite3 connect patch')
                database = args[0]
                dirname = os.path.dirname(database)
                if not os.path.exists(dirname):
                    logger.debug('creating non-existent directory {}'.format(dirname))
                    os.makedirs(dirname)
                if not os.path.exists(database):
                    open(database, 'a').close()
                for tries in range(10):
                    try:
                        return sqlite3_connect_orig(*args, **kwargs)
                    except:
                        time.sleep(1)
                        logger.exception('Failed to open DB')
                raise Exception('Failed to open DB file {}'.format(database))


            sqlite3.connect = sqlite3_connect_patch

            dbapi2_connect_orig = sqlite3.dbapi2.connect


            def dbapi2_connect_patch(*args, **kwargs):
                logger.debug('sqlite3.dbapi2 connect patch')
                database = args[0]
                dirname = os.path.dirname(database)
                if not os.path.exists(dirname):
                    logger.debug('creating non-existent directory {}'.format(dirname))
                    os.makedirs(dirname)
                if not os.path.exists(database):
                    open(database, 'a').close()
                for tries in range(10):
                    try:
                        return dbapi2_connect_orig(*args, **kwargs)
                    except:
                        time.sleep(1)
                        logger.exception('Failed to open DB')
                logger.exception('Failed to open DB file {}'.format(database))
                raise Exception('Failed to open DB file {}'.format(database))


            sqlite3.dbapi2.connect = dbapi2_connect_patch

            xbmcplugin.items = []
            imp.load_module(self.module, fp, self.dir, ('.py', 'rb', imp.PY_SOURCE))
        except:
            logger.exception('Failure in plugin run')
        sqlite3.connect = sqlite3_connect_orig
        sqlite3.dbapi2.connect = dbapi2_connect_orig
        urllib.quote_plus = quote_plus_orig
        fp.close()
        sys.path = orig
# sys.argv = old_sys_argv
        items = xbmcplugin.items
        logger.debug('Plugin {} ended with: {}'.format(self.name, items))

# some cleanup
        if self.id in xbmcaddon.ADDON_CACHE:
    # logger.debug('Saving settings {}'.format(xbmcaddon.ADDON_CACHE[self.id]))
            logger.debug('Saving settings')
            bridge._message({'type': 'saveSettings', 'addon': self.id, 'settings': xbmcaddon.ADDON_CACHE[self.id].settings})
        if hasattr(bridge, 'progress') and bridge.progress:
            logger.debug('Closing left over progress')
            bridge.closeprogress()
        ans = []
        items = xbmcplugin.items
        from Plugin import Item

        if len(items) == 1 and hasattr(items[0], 'path'):
            return items
        for item in items:
    # url, title, subtitle=None, icon=None, details=None, menuurl='', info={})
            i = Item(url=item['url'], title=convert_kodi_tags_to_html_tags(item['listitem'].label),
                 subtitle=item['listitem'].getProperty('subtitle'),
                icon=item['listitem'].thumbnailImage if item['listitem'].thumbnailImage != 'DefaultFolder.png' else '',
                details=item['listitem'].getProperty('details'), info=item['listitem'].infos,
                context=item['listitem'].context)
            if type(i.context) is list:  # needs to be dict
                i.context = {x[0]: x[1] for x in i.context}
            infos = item['listitem'].infos
            if 'poster' in infos:
                i.icon = infos['poster']
            if 'plot' in infos:
                i.details = infos['plot']
            if 'year' in infos:
                i.year = infos['year']
            if 'trailer' in infos:
                i.context['Watch trailer'] = 'RunPlugin({})'.format(infos['trailer'])
            # icon path fix
            if i.icon and i.icon.startswith(ADDONS_DIR):
                i.icon = i.icon.replace(ADDONS_DIR, '/addons')
            if i.icon:
                i.icon = i.icon.replace('\\', '/')
            ans.append(i)
        return ans
