from __future__ import division
import sys, os, imp, urllib, json, time, traceback, re, getopt, tempfile, AdvancedHTMLParser, urllib2, urlparse, zipfile, shutil, requests, logging, psutil, subprocess, sqlite3
from threading import Timer
from contextlib import contextmanager

VERSION='0.6'

try:
    from flask import Flask, render_template, send_from_directory, request, send_file, redirect
except:
    print 'TVML Server requires flask module.\nPlease install it via "pip install flask"'
    sys.exit(1)
try:
    import setproctitle
except:
    pass

import sqlite3

from packaging import version

# try:
# 	import faulthandler
# 	faulthandler.enable()
# except:
# 	print 'TVML Server requires faulthandler module.\nPlease install it via "pip install faulthandler"'
# 	sys.exit(1)

import multiprocessing
import urlparse

# import gevent.monkey
# gevent.monkey.patch_all()
try:
    from gevent.pywsgi import WSGIServer
    import gevent
except:
    print 'TVML Server requires gevent module.\nPlease install it via "pip install gevent"'
    sys.exit(1)

reload(sys)
sys.setdefaultencoding('utf8')

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = ''

DATA_DIR = os.path.join(os.path.expanduser("~"), '.TVMLSERVER')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.isdir(DATA_DIR):
    print '{} not a directory or cannot be created'.format(DATA_DIR)
    sys.exit(2)

if not os.path.exists(os.path.join(DATA_DIR, 'addons')):
    os.makedirs(os.path.join(DATA_DIR, 'addons'))
if not os.path.isdir(os.path.join(DATA_DIR, 'addons')):
    print '{} not a directory or cannot be created'.format(os.path.join(DATA_DIR, 'addons'))
    sys.exit(2)

if not os.path.exists(os.path.join(DATA_DIR, 'userdata')):
    os.makedirs(os.path.join(DATA_DIR, 'userdata'))
if not os.path.isdir(os.path.join(DATA_DIR, 'userdata')):
    print '{} not a directory or cannot be created'.format(os.path.join(DATA_DIR, 'userdata'))
    sys.exit(2)

if not os.path.exists(os.path.join(DATA_DIR, 'addons', 'packages')):
    os.makedirs(os.path.join(DATA_DIR, 'addons', 'packages'))
if not os.path.isdir(os.path.join(DATA_DIR, 'addons', 'packages')):
    print '{} not a directory or cannot be created'.format(os.path.join(DATA_DIR, 'addons', 'packages'))
    sys.exit(2)

if not os.path.exists(os.path.join(DATA_DIR, 'logs')):
    os.makedirs(os.path.join(DATA_DIR, 'logs'))
if not os.path.isdir(os.path.join(DATA_DIR, 'logs')):
    print '{} not a directory or cannot be created'.format(os.path.join(DATA_DIR, 'logs'))
    sys.exit(2)
LOGFILE = os.path.join(DATA_DIR, 'logs', 'tvmlserver.log')


if not os.path.exists(os.path.join(DATA_DIR, 'db')):
    os.makedirs(os.path.join(DATA_DIR, 'db'))
if not os.path.isdir(os.path.join(DATA_DIR, 'db')):
    print '{} not a directory or cannot be created'.format(os.path.join(DATA_DIR, 'db'))
    sys.exit(2)
DB_FILE = os.path.join(DATA_DIR, 'db', 'TVMLServer.db')


sys.path.append(os.path.join(bundle_dir, 'scripts'))
sys.path.append(os.path.join(bundle_dir, 'scripts', 'kodi'))
sys.path.append(os.path.join(DATA_DIR, 'addons'))

from scripts import kodi_utils
import jinja2

app = Flask(__name__, template_folder=os.path.join(bundle_dir, 'templates'))
app.jinja_env.filters['base64encode'] = kodi_utils.b64encode
app.config['JSON_AS_ASCII'] = False
from werkzeug.routing import PathConverter


class EverythingConverter(PathConverter):
    regex = '.*?'
app.url_map.converters['everything'] = EverythingConverter

@contextmanager
def open_db():
    global DB_FILE
    if not os.path.exists(DB_FILE):
        open(DB_FILE, 'w').close()
    for i in range(10):
        try:
            CONN = sqlite3.connect(DB_FILE)
        except:
            logger.exception('Failed to open DB')
            time.sleep(1)
    if not CONN:
        raise Exception('DB is locked')
    CONN.row_factory = sqlite3.Row
    DB = CONN.cursor()
    yield DB
    CONN.commit()
    DB.close()
    CONN.close()


from scripts.Plugin import Plugin, Item
from scripts.KodiPlugin import *
from scripts.bridge import bridge

from scripts import messages

from scripts import imageCache

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    filename=LOGFILE,
    filemode='w'
)
root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
logger = logging.getLogger('TVMLServer')


class MyProcess(multiprocessing.Process):
    def run(self):
        ans = self._target(*self._args, **self._kwargs)
        logger.debug('Process {} adding end message'.format(self.id))
        self.message({'type': 'end', 'ans': ans})
        self.onStop()
        self.stop.set()

    def response(self, id, response):
        logger.debug('Adding response on process {}'.format(self.id))
        self.responses.put({'id': id, 'response': response})

    def message(self, msg):
        self.messages.put(msg)

    def onStop(self):
        pass


def Process(group=None, target=None, name=None, args=(), kwargs={}):
    p = MyProcess(group, target, name, args, kwargs)
    p.messages = multiprocessing.Queue()
    p.responses = multiprocessing.Queue()
    p.stop = multiprocessing.Event()  # can be used to indicate stop
    p.id = str(id(p))
    return p


def update_addons():
    for row in get_all_installed_addons():
        try:
            current_version = row['version']
            found = find_addon(row['id'])
            if not found:
                continue
            available_version = found[0]['version']
            if version.parse(current_version) < version.parse(available_version):
                logger.info(
                    'Found update for addon {}. Current version: {}, Available version: {}'.format(row['id'], current_version,
                                                                                                available_version))
                remove_addon(row['id'])
                install_addon(found[0])
        except:
            logger.exception('Failed to update addon {}'.format(row['id']))

def fix_addons():
    repeat = True
    while repeat:
        repeat = False
        for row in get_all_installed_addons():
            try:
                for r in json.loads(row['requires']):
                    if not get_installed_addon(r):
                        found = find_addon(r)
                        if found:
                            install_addon(found[0])
                            repeat = True
                        else:
                            logger.error('Addon {} is required by addon {} and cannot be found'.format(r, row['id']))
            except:
                logger.exception('Failed to fix addon {}'.format(row['id']))



@app.route('/response/<pid>/<id>', methods=['POST', 'GET'])
@app.route('/response/<pid>/<id>/<res>')
def route(pid, id, res=None):
    if request.method == 'POST':
        res = request.form.keys()[0]
    global PROCESSES
    if pid in PROCESSES:
        p = PROCESSES[pid]
        logger.debug('received response on process {}'.format(pid))
        if p is not None:
            p.responses.put({'id': id, 'response': res})
            return 'OK', 204
        return render_template('alert.xml', title='Communication error',
                               description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
    else:
        return 'OK', 204


@app.route('/icon.png')
def icon():
    return send_from_directory(bundle_dir, 'icon.png')


PROXY=False

@app.route('/cache/<id>')
def cache(id):
    if PROXY:
        file = imageCache.get(id)
        if file:
            return send_file(file)
        else:
            return 'Not found', 404
    else:
        url = kodi_utils.b64decode(id)
        return redirect(url)


@app.route('/toggleProxy')
def toggle_proxy():
    global PROXY
    PROXY = not PROXY
    return 'OK', 206

@app.route('/addons/<path:filename>')
def kodiplugin_icon(filename):
    return send_from_directory(os.path.join(DATA_DIR, 'addons'), filename)


@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory(os.path.join(bundle_dir, 'js'), filename)


@app.route('/templates/<path:filename>')
def template(filename):
    return send_from_directory(os.path.join(bundle_dir, 'templates'), filename)


@app.route('/menu/<pluginid>', methods=['POST', 'GET'])
@app.route('/menu/<pluginid>/<process>', methods=['POST', 'GET'])
@app.route('/catalog/<pluginid>', methods=['POST', 'GET'])
@app.route('/catalog/<pluginid>/<process>', methods=['POST', 'GET'])
# @app.route('/catalog/<pluginid>/<url>')
# @app.route('/catalog/<pluginid>/<url>/<process>')
def catalog(pluginid, process=None):
    url = None
    LANGUAGE='English'
    settings = None
    history = None
    if request.method == 'POST':
        try:
            post_data = json.loads(kodi_utils.b64decode(request.form.keys()[0]))
            #logger.debug(post_data)
            favs_json = json.loads(post_data['favs'])
            url = post_data['url']
            LANGUAGE = post_data['lang']
            settings = post_data['settings']
            #history = json.loads(post_data['history'])
        except:
            logger.exception('Failed to parse post data')
            url = request.form.keys()[0]

    try:
        if not url:
            decoded_url = ''
        elif url == 'fake':
            decoded_url = ''
        else:
            decoded_url = kodi_utils.b64decode(url)
        decoded_id = kodi_utils.b64decode(pluginid)
        if request.full_path.startswith('/catalog'):
            logger.debug('catalog {}, {}, {}'.format(decoded_id, decoded_url, process))
        else:
            logger.debug('menu {}, {}'.format(decoded_id, process))
        plugin = get_installed_addon(decoded_id)
        if not plugin:
            return render_template('alert.xml', title='Missing plugin',
                                   description="Failed to run plugin {}.\nYou may need to install it manually".format(decoded_id))

        global PROCESSES
        if process:
            if not process in PROCESSES:
                return render_template('alert.xml', title='Fatal error',
                                       description="Failed to load page.\nSomething has gone terribly wrong.\nPlease try to restart the App")
            p = PROCESSES[process]
        else:
            if request.full_path.startswith('/catalog'):
                p = Process(target=get_items, args=(plugin['id'], decoded_url, CONTEXT, LANGUAGE, settings))
            else:
                p = Process(target=get_menu, args=(plugin['id'], decoded_url, LANGUAGE, settings))
            logger.debug('saving process id {}'.format(p.id))
            PROCESSES[p.id] = p

            def stop():
                time.sleep(5)  # close bridge after 5s
                global PROCESSES
                del PROCESSES[p.id]

            # b.thread.onStop = stop
            p.start()
        logger.debug('entering while alive')
        try:
            while p.is_alive():
                try:
                    msg = p.messages.get(False)
                except:
                    gevent.sleep(0.1)
                    continue
                try:
                    method = getattr(messages, msg['type'])
                    if msg['type'] == 'end':
                        if not p.messages.empty():
                            logger.warning('Got end message but queue not empty. Getting another')
                            p.messages.put(msg)
                            continue
                        global PROCESSES
                        for t in PROCESSES:
                            PROCESSES[t].responses.close()
                            PROCESSES[t].messages.close()
                            del PROCESSES[t].responses
                            del PROCESSES[t].messages
                            del PROCESSES[t].stop
                            PROCESSES[t]._popen.terminate()
                        PROCESSES.clear()
                        # p.join()
                        # p.terminate()
                        logger.debug('PROCESS {} TERMINATED'.format(p.id))
                    return_url = None
                    if process:
                        # return on same url for more
                        return_url = request.url
                    else:
                        # add response bridge
                        return_url = '{}/{}'.format(request.url, p.id)
                    # else:
                    # No url and no response so add 'fake' url
                    #	return_url = '{}/{}/{}'.format(request.url, 'fake', p.id)
                    return method(plugin, msg, return_url, decoded_url, history)
                except:
                    logger.exception('Error in while alive')
        except:
            logger.exception('Error in while alive')
        logger.debug('exiting while alive and entering 5s wait')
        # Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
        start = 0
        while start < 5:  # wait at most 5 seconds
            try:
                msg = p.messages.get(False)
            except:
                gevent.sleep(0.1)
                start += 0.1
                continue
            try:
                method = getattr(messages, msg['type'])
                if msg['type'] == 'end':
                    if not p.messages.empty():
                        logger.warning('Got end message but queue not empty. Getting another')
                        p.messages.put(msg)
                        continue
                    global PROCESSES
                    for t in PROCESSES:
                        PROCESSES[t].responses.close()
                        PROCESSES[t].messages.close()
                        del PROCESSES[t].responses
                        del PROCESSES[t].messages
                        del PROCESSES[t].stop
                        PROCESSES[t]._popen.terminate()
                    PROCESSES.clear()
                    # p.join()
                    # p.terminate()
                    logger.debug('PROCESS {} TERMINATED'.format(p.id))
                return method(plugin, msg, request.url, decoded_url, history) if process else method(plugin, msg,
                                                                               '{}/{}'.format(request.url, p.id), decoded_url, history)
            except:
                logger.exception('Error while waiting for process messages after death')
        logger.debug('finished 5 sec wait')
        # if we got here, this means thread has probably crashed.
        global PROCESSES
        if p.id in PROCESSES:
            del PROCESSES[p.id]
        try:
            p.join()
            p.terminate()
        except:
            logger.exception('Process not found or cannot be killed')
        logger.error('PROCESS {} CRASHED'.format(p.id))

        return render_template('alert.xml', title='Communication error',
                               description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
    except:
        logger.exception('Error in catalog')
        return render_template('alert.xml', title='Communication error',
                               description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")


@app.route('/main', methods=['POST'])
def main():
    favs = []
    try:
        post_data = json.loads(kodi_utils.b64decode(request.form.keys()[0]))
        favs_json = json.loads(post_data['favs'])
        clear_favorites()
        for id in favs_json:
            addon = get_installed_addon(id)
            if not addon:
                logger.warning('No match found for favorite addon {}'.format(id))
                continue  # no match found
            set_installed_addon_favorite(id, True)
        global LANGUAGE
        LANGUAGE = post_data['lang']
        global PROXY
        PROXY = True if post_data['proxy'] == 'true' else False
    except:
        pass

    filtered_plugins =  [p for p in get_all_installed_addons() if [val for val in json.loads(p['type']) if val in ['Video', 'Audio']]] #Show only plugins with video/audio capability since all others are not supported
    fav_plugins = [p for p in filtered_plugins if p['favorite']]
    return render_template('main.xml', menu=filtered_plugins, favs=fav_plugins, url=request.full_path, proxy='On' if PROXY else 'Off', version=VERSION, languages=["Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Azerbaijani", "Basque", "Belarusian", "Bosnian", "Bulgarian", "Burmese", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Esperanto", "Estonian", "Faroese", "Finnish", "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Malayalam", "Maltese", "Maori", "Mongolian", "Norwegian", "Ossetic", "Persian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Silesian", "Sinhala", "Slovak", "Slovenian", "Spanish", "Spanish", "Swedish", "Tajik", "Tamil", "Telugu", "Thai", "Turkish", "Ukrainian", "Uzbek", "Vietnamese", "Welsh"], current_language=LANGUAGE)

@app.route('/setLanguage', methods=['POST'])
def set_language():
    try:
        global LANGUAGE
        LANGUAGE = kodi_utils.b64decode(request.form.keys()[0])
    except:
        logger.exception('Failed to set language')
    return '', 204


@app.route('/removeAddon', methods=['POST'])
def removeAddon():
    try:
        if request.method == 'POST':
            id = kodi_utils.b64decode(request.form.keys()[0])
            found = get_installed_addon(id)
            if found:
                remove_addon(id)
        #return json.dumps({'url': '/main', 'replace': True, 'initial': True}), 212 #Reload main screen
        return render_template('alert.xml', title='Succcess', description='Successfully removed addon {}'.format(found['name']))
    except:
        traceback.print_exc(file=sys.stdout)
        #return 'NOTOK', 206
        return render_template('alert.xml', title='Failed',
                               description='Failed to remove addon {}'.format(found['name']))


def remove_addon(id):
    logger.debug('deleting plugin {}'.format(id))
    addon = get_installed_addon(id)
    if addon:
        if 'Repository' in json.loads(addon['type']):
            global REPOSITORIES
            index_to_del = None
            for (i,j) in enumerate(REPOSITORIES):
                if j['name'] == addon['name']:
                    index_to_del = i
            if index_to_del:
                del REPOSITORIES[index_to_del]
            global REFRESH_EVENT
            REFRESH_EVENT.clear()
            multiprocessing.Process(target=get_available_addons, args=(REPOSITORIES, REFRESH_EVENT)).start()
    path = os.path.join(DATA_DIR, 'addons', id)
    try:
        shutil.rmtree(path)
    except:
        pass
    with open_db() as DB:
        DB.execute('delete from INSTALLED where id=?', (id,))


def get_items(plugin_id, url, context, LANGUAGE, settings):
    if 'setproctitle' in sys.modules:
        setproctitle.setproctitle('python TVMLServer ({}:{})'.format(plugin_id, url))
    kodi_utils.windows_pyinstaller_multiprocess_hack()
    logger = logging.getLogger(plugin_id)
    logger.debug('Getting items for: {}'.format(url))

    try:
        plugin = KodiPlugin(plugin_id)
        if not plugin:
            raise Exception('could not load plugin')
        b = bridge()
        b.context = context
        items = plugin.run(b, url, LANGUAGE, settings)
        del plugin
        del b
        del logger
    except:
        logger.exception('Encountered error in plugin: {}'.format(plugin_id))
        items = None
    # logger.debug('get_items finished with {}'.format(items))
    return items


def get_menu(plugin_id, url, LANGUAGE, settings):
    print('Getting menu for: {}'.format(url))
    url = url.split('?')[1] if '?' in url else url
    try:
        plugin = KodiPlugin(plugin_id)
        if not plugin:
            raise Exception('could not load plugin')
        b = bridge()
        items = plugin.settings(b, url, LANGUAGE, settings)
    except:
        logger.exception('Encountered error in plugin: {}'.format(plugin_id))
        items = None
    return items


def get_settings():
    logger.debug('getting settings')
    try:
        b = bridge()
    except:
        logger.exception('Encountered error in settings')


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def get_available_addons(REPOSITORIES, e=None):
    logger.debug('Refreshing repositories. Please wait...')
    with open_db() as DB:
        DB.execute('delete from ADDONS')
    for r in REPOSITORIES:
        temp = []
        for dir in r['dirs']:
            try:
                req = requests.get(dir['xml'])
                link = req.text
                parsed = parse_addon_xml(link, r, dir)
                parsed = [(addon['id'], r['name'], json.dumps(dir), json.dumps(addon['type']), addon['name'], json.dumps(addon['data']), addon['version'], addon['script'], json.dumps(addon['requires']), addon['icon']) for addon in parsed]
                temp += parsed
            except:
                logger.exception('Cannot read repository {}'.format(r['name']))
        with open_db() as DB:
            try:
                DB.executemany('insert into ADDONS values(?,?,?,?,?,?,?,?,?,?)', temp)
            except:
                logger.exception('failed to insert addons into DB')
    logger.debug('Finished refreshing repositories')
    fix_addons()
    update_addons()
    if e:
        e.set()


@app.route('/installAddon', methods=['POST'])
def installAddon():
    if request.method == 'POST':
        try:
            id = kodi_utils.b64decode(request.form.keys()[0])
            already_installed = get_installed_addon(id)
            if already_installed:
                return render_template('alert.xml', title='Already installed',
                                       description="This addon is already installed")
            found = find_addon(id)
            if not found:
                return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
            install_addon(found[0])
            plugin = KodiPlugin(id)
            for r in plugin.requires:
                already_installed = get_installed_addon(r)
                if already_installed:
                    continue
                found = find_addon(r)
                if not found:
                    return render_template('alert.xml', title='Unknown addon', description="This addon has a requirement that cannot be found {}".format(r))
                install_addon(found[0])
            #return json.dumps({'url': '/main', 'replace': True, 'initial': True}), 212  # Reload main screen
            return render_template('alert.xml', title='Installation complete',
                                   description="Successfully installed addon {}".format(
                                       plugin.name))
        except:
            logger.exception('Failed to download/install {}'.format(id))
            try:
                remove_addon(id)
            except:
                pass
            return render_template('alert.xml', title='Install error',
                                   description="Failed to install addon.\nThis could be due to a network error or bad repository parsing")
    return render_template('alert.xml', title='URL error', description='This URL is invalid')


def find_addon(id):
    """Gets all rows of available addons with same id sorted by version from highest to lowest"""
    found = []
    with open_db() as DB:
        for row in DB.execute('select * from ADDONS where id=?', (id,)):
            found.append(row)

    def cmp(a, b):
        a_version = a['version']
        b_version = b['version']
        if version.parse(a_version) < version.parse(b_version):
            return 1
        if version.parse(a_version) == version.parse(b_version):
            return 0
        return -1

    found = sorted(found, cmp=cmp)
    return found

def get_installed_addon(id):
    """Gets the row of the addon if its installed"""
    with open_db() as DB:
        row = DB.execute('select * from INSTALLED where id=?', (id,)).fetchone()
        return row

def set_installed_addon_favorite(id, fav):
    """Updates the favorite column of the installed addon in the DB"""
    with open_db() as DB:
        if fav:
            DB.execute('update INSTALLED set favorite=1 where id=?',(id,))
        else:
            DB.execute('update INSTALLED set favorite=0 where id=?', (id,))


def clear_favorites():
    with open_db() as DB:
        DB.execute('update INSTALLED set favorite=0')


def get_all_installed_addons():
    """Returns a list of rows from DB of all installed addons"""
    with open_db() as DB:
        found = []
        for row in DB.execute('select * from INSTALLED'):
            found.append(row)
    return found



def install_addon(addon):
    logger.debug('Installing addon {}'.format(addon['id']))
    download_url = '{0}/{1}/{1}-{2}.zip'.format(json.loads(addon['dir'])['download'], addon['id'], addon['version'])
    logger.debug('downloading plugin {}'.format(download_url))
    temp = os.path.join(tempfile.gettempdir(), '{}.zip'.format(addon['id']))
    r = requests.get(download_url, stream=True)
    if not r.status_code == 200:
        raise Exception('Failed to download')
    with open(temp, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)
    if not zipfile.is_zipfile(temp):
        raise Exception('failed to download')
    path = os.path.join(DATA_DIR, 'addons')
    with zipfile.ZipFile(temp, 'r') as zip:
        zip.extractall(path)
    with open_db() as DB:
        DB.execute('insert into INSTALLED VALUES(?,?,?,?,?,?,?,?,0)', (addon['id'], addon['type'], addon['name'], addon['data'], addon['version'], addon['script'], addon['requires'], addon['icon']))


@app.route('/getAddonData', methods=['POST'])
def getAddonData():
    try:
        id = kodi_utils.b64decode(request.form.keys()[0])
        found = get_installed_addon(id)
        if found:
            addon = dict(found)
            addon['installed'] = True
        else:
            found = find_addon(id)
            if found:
                addon = dict(found[0])
        if not addon:
            return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
        addon['type'] = json.loads(addon['type'])
        #addon['dir'] = json.loads(addon['dir'])
        addon['data'] = json.loads(addon['data'])
        addon['requires'] = json.loads(addon['requires'])
        return render_template('addonDetails.xml', addon=addon)
    except:
        logger.exception('Failed to get data on {}'.format(id))
        return render_template('alert.xml', title='Error',
                               description="Failed to get data on addon.\nThis could be due to a network error or bad repository parsing")

@app.route('/refreshRepositories')
def refresh_repositories():
    global REFRESH_EVENT
    if REFRESH_EVENT.is_set(): #i.e. refresh not in progress
        REFRESH_EVENT.clear()
        multiprocessing.Process(target=get_available_addons, args=(REPOSITORIES, REFRESH_EVENT)).start()
    gevent.sleep(1)
    return json.dumps({'url': '/refreshProgress'}), 212

@app.route('/refreshProgress')
def refresh_progress():
    if not REFRESH_EVENT.is_set():
        gevent.sleep(1)
        return render_template('progressdialog.xml', title='Please wait', text='Refreshing repositories. This may take some time', value='0', url='/refreshProgress'), 214
    return '', 206

@app.route('/viewLog')
def viewLog():
    with open(LOGFILE, 'r') as f:
        log = f.readlines()
        log.reverse()
        return render_template('logTemplate.xml', title='TVMLServer log', text=''.join(log))


@app.route('/clearLog')
def clear_log():
    open(LOGFILE, 'w').close()


@app.route('/checkForUpdate')
def check_for_update():
    try:
        req = requests.get('https://api.github.com/repos/ggyeh/TVML-Kodi-Addons/releases/latest')
        json = req.json()
        latest = json['tag_name']
        current = VERSION
        if latest != current:
            return render_template('alert.xml', title='Update found', description='New version detected {}\nCurrent version is {}\n\nSorry, no auto-update yet.\nPlease visit https://github.com/ggyeh/TVML-Kodi-Addons/releases/latest to download'.format(latest, current))
        else:
            return render_template('alert.xml', title='Up to date',
                           decsription='You are running the latest version')
    except:
        return render_template('alert.xml', title='UError',
                               decsription='Failed to check for new version')


@app.route('/restart')
def restart():
    print 'restarting app'
    global http_server
    http_server.stop()
    # try:
    #	p = psutil.Process(os.getpid())
    #	for handler in p.open_files() + p.connections():
    #		os.close(handler.fd)
    # except Exception, e:
    #	print e
    exe = sys.executable
    subprocess.Popen([exe] + sys.argv)
    # os.execl(python, python, *sys.argv)
    sys.exit(0)


@app.route('/repositories')
def respositories():
    return render_template('repositories.xml', title='Repositories', repositories=[r['name'] for r in REPOSITORIES])


@app.route('/addonsForRepository', methods=['POST'])
def addonsForRepository():
    try:
        if not REFRESH_EVENT.is_set():
            gevent.sleep(1)
            return render_template('progressdialog.xml', title='Please wait', text='Refreshing repositories. This may take some time', value='0', url='/addonsForRepository', data=request.form.keys()[0]), 214
        name = kodi_utils.b64decode(request.form.keys()[0])
        with open_db() as DB:
            repo_addons = [row for row in DB.execute('select * from ADDONS where repo=?', (name,))]
        addons = {}
        for a in repo_addons:
            b = dict(a)
            b['type'] = json.loads(b['type'])
            b['dir'] = json.loads(b['dir'])
            b['data'] = json.loads(b['data'])
            b['requires'] = json.loads(b['requires'])
            for type in b['type']:
                if not type in addons:
                    addons[type] = []
                addons[type].append(b)

        for type in addons:
            addons[type] = sorted(addons[type], key=lambda a: a['name'])

        return render_template('addonsList.xml', addons=addons)
    except Exception as e:
        logger.exception('Failed to show addons by repository {}'.format(name))
        return render_template('alert.xml', title='Error', description='{}'.format(e))


@app.route('/addRepository', methods=['POST'])
def addRepository():
    try:
        path = kodi_utils.b64decode(request.form.keys()[0])
        if not os.path.exists(path):
            return render_template('alert.xml', title='Error', description='{} does not exist'.format(path))
        if not os.path.isfile(path):
            return render_template('alert.xml', title='Error', description='{} is not a valid file'.format(path))
        if not zipfile.is_zipfile(path):
            return render_template('alert.xml', title='Error', description='{} is not a valid zipfile'.format(path))
        with zipfile.ZipFile(path, 'r') as zip:
            xml = [f for f in zip.namelist() if f.endswith('addon.xml')][0]
            dir = os.path.join(DATA_DIR, 'addons')
            zip.extractall(dir)
        xml = os.path.join(DATA_DIR, 'addons', xml)
        with open(xml, 'r') as f:
            repo = {}
            parser = AdvancedHTMLParser.Parser.AdvancedHTMLParser()
            parser.feed(f.read())
            repo['name'] = parser.getElementsByTagName('addon')[0].attributes['name']
            repo['dirs'] = []
            infos = parser.getElementsByTagName('info')
            datadirs = parser.getElementsByTagName('datadir')
            if len(infos) != len(datadirs):
                raise Exception('Failed to parse addon.xml')
            for i in range(len(infos)):
                repo['dirs'].append({'xml': infos[i].text, 'download': datadirs[i].text})
            global REPOSITORIES
            if repo['name'] in [r['name'] for r in REPOSITORIES]:
                return render_template('alert.xml', title='Already exists', description='Repository with this name already exists')
            REPOSITORIES.append(repo)
            global REFRESH_EVENT
            REFRESH_EVENT.clear()
            multiprocessing.Process(target=get_available_addons, args=(REPOSITORIES, REFRESH_EVENT)).start()
            return json.dumps({'url': '/main', 'replace': True, 'initial': True}), 212  # Reload main screen
    except Exception as e:
        logger.exception('Failed to add repository {}'.format(path))
        return render_template('alert.xml', title='Error', description='{}'.format(e))


@app.route('/browseAddons', methods=['POST', 'GET'])
def browse_addons():
    """This method will return all available addons by type"""
    search = None
    if request.method == 'POST':
        search='.*{}.*'.format(request.form.keys()[0])
    if not REFRESH_EVENT.is_set():
        gevent.sleep(1)
        return render_template('progressdialog.xml', title='Please wait', text='Refreshing repositories. This may take some time', value='0', url='/browseAddons'), 214
    with open_db() as DB:
        rows = [row for row in DB.execute('select * from ADDONS')]
    all = {}
    for row in rows:
        if search:
            if not re.match(search, row['name']) and not re.match(search, row['id']):
                continue
        row = dict(row)
        row['types'] = json.loads(row['type'])
        installed = 1 if get_installed_addon(row['id']) else 0
        row['installed'] = installed
        row['dir'] = json.loads(row['dir'])
        row['requires'] = json.loads(row['requires'])
        for type in row['types']:
            if not type in all:
                all[type] = []
            all[type].append(row)
    return render_template('addonsList.xml', addons=all)


@app.route('/allAddons')
def all_addons():
    """This method will return all available addons in a search template"""
    if not REFRESH_EVENT.is_set():
        gevent.sleep(1)
        return render_template('progressdialog.xml', title='Please wait', text='Refreshing repositories. This may take some time', value='0', url='/browseAddons'), 214
    with open_db() as DB:
        rows = [row for row in DB.execute('select * from ADDONS')]
    all = {}
    for row in rows:
        row = dict(row)
        row['types'] = json.loads(row['type'])
        installed = 1 if get_installed_addon(row['id']) else 0
        row['installed'] = installed
        row['dir'] = json.loads(row['dir'])
        row['requires'] = json.loads(row['requires'])
        if row['id'] in all: #if already exists with same id
            if version.parse(all[row['id']]['version']) < version.parse(row['version']): #if found higher version
                all[row['id']] = row #overrite newer version
        else:
            all[row['id']] = row
    return render_template('addons.xml', all=all)

last_dir = os.path.expanduser("~")
@app.route('/browse', methods=['GET', 'POST'])
def browse():
    dir = None
    filter = None
    if request.method == 'POST':
        post_data = json.loads(kodi_utils.b64decode(request.form.keys()[0]))
        dir = kodi_utils.b64decode(post_data['dir']) if post_data['dir'] else ''
        filter = post_data['filter']
        print 'browsing to {}'.format(dir)
    global last_dir
    if not dir:
        dir = last_dir
    last_dir = dir
    try:
        if os.path.isdir(dir):
            files = [{'url': kodi_utils.b64encode(os.path.join(dir, f)), 'title': f} for f in os.listdir('{}'.format(dir))]
            if filter:
                files = [f for f in files if os.path.isdir(kodi_utils.b64decode(f['url'])) or re.match(filter, f['title'])]
            up = kodi_utils.b64encode(os.path.dirname(dir))
            return render_template('browse.xml', title=dir, files=files, up=up)
        else:
            return dir, 218
    except:
        logger.exception('Failed to browse {}'.format(dir))
        return render_template('alert.xml', title='Error', description='Failed to browse {}'.format(dir))


def help(argv):
    print 'Usage: {} [-p <port>] [-d <dir>]'.format(argv[0])
    print
    print '-p <port>, --port=<port>		Run the server on <port>. Default is 5000'
    print '-t <dir>, --temp=<dir>			Specify alternate temp directory. Default is {}'.format(tempfile.gettempdir())
    sys.exit()


def mmain(argv):
    port = 5000  # default

    try:
        opts, args = getopt.getopt(argv[1:], "hp:t:", ["port=", "temp="])
    except getopt.GetoptError:
        help(argv)
    for opt, arg in opts:
        if opt == '-h':
            help(argv)
        elif opt in ("-p", "--port"):
            try:
                port = int(arg)
            except:
                print '<port> option must be an integer'
                sys.exit(2)
        elif opt in ("-t", "--temp"):
            if os.path.isdir(arg):
                tempfile.tempdir = arg
            else:
                print '{} is not a valid directory'.format(arg)
                sys.exit(2)

    manager = multiprocessing.Manager()


    global PROCESSES
    PROCESSES = {}

    global CONTEXT
    CONTEXT = manager.dict()

    global REPOSITORIES
    REPOSITORIES = [
        {'name': 'Kodi repository', 'dirs': [{'xml': 'http://mirrors.kodi.tv/addons/krypton/addons.xml',
                                              'download': 'http://mirrors.kodi.tv/addons/krypton'}]},
        {'name': 'Kodi Israel', 'dirs': [{'xml': 'https://raw.githubusercontent.com/kodil/kodil/master/addons.xml',
                                          'download': 'https://raw.githubusercontent.com/kodil/kodil/master/repo'}]},
        #{'name': 'Exodus repository',
        # 'dirs': [{'xml': 'https://offshoregit.com/exodus/addons.xml', 'download': 'https://offshoregit.com/exodus/'}]}
    ]

    with open_db() as DB:
        DB.execute('drop table if exists ADDONS')
        DB.execute('create table ADDONS(id text, repo text, dir text, type text, name text, data text, version text, script text, requires text, icon text)')
        DB.execute('drop table if exists INSTALLED')
        DB.execute('create table INSTALLED(id text primary_key, type text, name text, data text, version text, script text, requires text, icon text, favorite integer default 0)')

        for plugin in os.listdir(os.path.join(DATA_DIR, 'addons')):
            try:
                dir = os.path.join(DATA_DIR, 'addons', plugin)
                if not os.path.isdir(dir):
                    continue
                logger.debug('Loading kodi plugin {}'.format(plugin))
                p = KodiPlugin(plugin)
                #if [val for val in p.type if val in ['Video', 'Audio', 'Repository']]:
                if 'Repository' in p.type: #Need additional stuff
                    try:
                        with open(os.path.join(DATA_DIR, 'addons', plugin, 'addon.xml'), 'r') as f:
                            repo = {}
                            parser = AdvancedHTMLParser.Parser.AdvancedHTMLParser()
                            parser.feed(f.read())
                            repo['name'] = parser.getElementsByTagName('addon')[0].attributes['name']
                            repo['dirs'] = []
                            infos = parser.getElementsByTagName('info')
                            datadirs = parser.getElementsByTagName('datadir')
                            if len(infos) != len(datadirs):
                                raise Exception('Failed to parse addon.xml')
                            for i in range(len(infos)):
                                repo['dirs'].append({'xml': infos[i].text, 'download': datadirs[i].text})
                            #check if already exists
                            if not [d for d in repo['dirs'] if d not in [i for j in [r['dirs'] for r in REPOSITORIES] for i in j]]:
                                #we have no dirs that don't already exists
                                continue
                            REPOSITORIES.append(repo)
                    except:
                        logger.exception('Failed to parse installed repository {}'.format(plugin))
                DB.execute('insert into INSTALLED VALUES(?,?,?,?,?,?,?,?,0)', (p.id, json.dumps(p.type), unicode(p.name), json.dumps(p.data), p.version, p.script, json.dumps(p.requires), p.icon))
                logger.debug('Successfully loaded plugin: {}'.format(p))
            except Exception as e:
                logger.error('Failed to load kodi plugin {}. Error: {}'.format(plugin, e))

    global http_server
    http_server = WSGIServer(('', port), app)
    import socket
    try:
        addr = socket.gethostbyname(socket.gethostname())
    except:
        addr = socket.gethostname()

    global REFRESH_EVENT
    REFRESH_EVENT = multiprocessing.Event()
    multiprocessing.Process(target=get_available_addons, args=(REPOSITORIES, REFRESH_EVENT)).start()

    print
    print 'Server now running on port {}'.format(port)
    print 'Connect your TVML client to: http://{}:{}'.format(addr, port)
    # http_server.log = open('http.log', 'w')
    http_server.serve_forever()


# app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':

    multiprocessing.freeze_support()

    kodi_utils.windows_pyinstaller_multiprocess_hack()
    #  	import pystray
    #  	from PIL import Image, ImageDraw
    #  	width=30
    #  	height=30
    #  	color1='red'
    #  	color2='blue'
    #
    #  	image = Image.new('RGB', (width, height), color1)
    #  	dc = ImageDraw.Draw(image)
    #  	dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
    #  	dc.rectangle((0, height // 2, width // 2, height), fill=color2)
    #
    #
    #  	def f(*args):
    # 	 	print 'stopping http server'
    #  		http_server.stop()
    #  		server_process.join()
    #  		print 'http server stopped'
    #  		server_process = multiprocessing.Process(target=http_server.serve_forever, args=()).start()
    #
    #  	menu = pystray.MenuItem('Restart server', f)
    #
    #
    #
    #  	icon = pystray.Icon('test name', image, menu=[menu])
    #
    #  	def setup(icon):
    #  	    icon.visible = True
    #  	    mmain(sys.argv)
    #
    # 	icon.run(setup)
    mmain(sys.argv)