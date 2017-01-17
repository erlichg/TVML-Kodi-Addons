from __future__ import division
import sys, os, imp, urllib, json, time, traceback, re, getopt, tempfile, AdvancedHTMLParser, urllib2, urlparse, zipfile, shutil, requests, logging, psutil, subprocess, sqlite3
from threading import Timer
from contextlib import contextmanager

try:
    from flask import Flask, render_template, send_from_directory, request, send_file
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


LANGUAGE = 'English'

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
    CONN = sqlite3.connect(os.path.join(tempfile.gettempdir(), 'TVMLServer.db'))
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
        logger.debug('Thread adding end message')
        self.message({'type': 'end', 'ans': ans})
        self.onStop()
        self.stop = True

    def response(self, id, response):
        self.responses.put({'id': id, 'response': response})

    def message(self, msg):
        self.messages.put(msg)

    def onStop(self):
        pass


def Process(group=None, target=None, name=None, args=(), kwargs={}):
    p = MyProcess(group, target, name, args, kwargs)
    p.messages = multiprocessing.Queue()
    p.responses = multiprocessing.Queue()
    p.stop = False  # can be used to indicate stop
    p.id = str(id(p))
    return p


def update_addons():
    global PLUGINS
    for p in PLUGINS:
        try:
            current_version = p.version
            found = find_addon(p.id)
            if not found:
                continue
            available_version = found[0]['version']
            if version.parse(current_version) < version.parse(available_version):
                logger.info(
                    'Found update for addon {}. Current version: {}, Available version: {}'.format(p.id, current_version,
                                                                                                available_version))
                remove_addon(p.id)
                install_addon(found[0])
                plugin = KodiPlugin(p.id)
                for i2, p2 in enumerate(PLUGINS):
                    if p2.id == p.id:
                        del PLUGINS[i2]
                        PLUGINS.append(plugin)
                        break
        except:
            logger.exception('Failed to update addon {}'.format(p.id))


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


@app.route('/cache/<id>')
def cache(id):
    file = imageCache.get(id)
    if file:
        return send_file(file)
    else:
        return 'Not found', 404


@app.route('/addons/<path:filename>')
def kodiplugin_icon(filename):
    return send_from_directory(os.path.join(DATA_DIR, 'addons'), filename)


@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory(os.path.join(bundle_dir, 'js'), filename)


@app.route('/templates/<path:filename>')
def template(filename):
    return send_from_directory(os.path.join(bundle_dir, 'templates'), filename)


@app.route('/menu/<pluginid>')
@app.route('/menu/<pluginid>/<process>')
@app.route('/catalog/<pluginid>', methods=['POST', 'GET'])
@app.route('/catalog/<pluginid>/<process>', methods=['POST', 'GET'])
# @app.route('/catalog/<pluginid>/<url>')
# @app.route('/catalog/<pluginid>/<url>/<process>')
def catalog(pluginid, process=None):
    url = None
    if request.method == 'POST':
        try:
            url = request.form.keys()[0]
        except:
            url = None
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
        plugin = [p for p in PLUGINS if p.id == decoded_id][0]
        if not plugin:
            return render_template('alert.xml', title='Communication error',
                                   description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")

        global PROCESSES
        if process:
            if not process in PROCESSES:
                return render_template('alert.xml', title='Fatal error',
                                       description="Failed to load page.\nSomething has gone terribly wrong.\nPlease try to restart the App")
            p = PROCESSES[process]
        else:
            if request.full_path.startswith('/catalog'):
                p = Process(target=get_items, args=(plugin.id, decoded_url, CONTEXT, PLUGINS, LANGUAGE))
            else:
                p = Process(target=get_menu, args=(plugin.id, decoded_url, PLUGINS, LANGUAGE))
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
                        global PROCESSES
                        del PROCESSES[p.id]
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
                    return method(plugin, msg, return_url)
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
                    global PROCESSES
                    del PROCESSES[p.id]
                    # p.join()
                    # p.terminate()
                    logger.debug('PROCESS {} TERMINATED'.format(p.id))
                return method(plugin, msg, request.url) if process else method(plugin, msg,
                                                                               '{}/{}'.format(request.url, p.id))
            except:
                traceback.print_exc(file=sys.stdout)
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
        logger.debug(post_data)
        favs_json = json.loads(post_data['favs'])
        for id in favs_json:
            matching = [p for p in PLUGINS if p.id == id]
            if len(matching) == 0:
                logger.warning('No match found for favorite addon {}'.format(id))
                continue  # no match found
            if len(matching) == 1:
                favs.append(matching[0])
                continue
            logger.warning('More than one addons found that match id {}. Skipping'.format())
        global LANGUAGE
        LANGUAGE = post_data['lang']
    except:
        pass

    if not REFRESH_EVENT.is_set():
        gevent.sleep(1)
        return render_template('progressdialog.xml', title='Please wait', text='Refreshing repositories. This may take some time', value='0', url='/main', data=request.form.keys()[0]), 214
    print 'rendering template with favs={}'.format(favs)
    with open_db() as DB:
        all = [row for row in DB.execute('select * from AVAILABLE_ADDONS')]
    all = {a['id']:a for a in all if [val for val in json.loads(a['type']) if val in ['Video', 'Audio', 'Repository']]}
    return render_template('main.xml', menu=PLUGINS, favs=favs, url=request.full_path,
                           all=all)


@app.route('/removeAddon', methods=['POST'])
def removeAddon():
    try:
        if request.method == 'POST':
            id = kodi_utils.b64decode(request.form.keys()[0])
            remove_addon(id)
        return json.dumps({'url': '/main', 'replace': True, 'initial': True}), 212
    except:
        traceback.print_exc(file=sys.stdout)
        return 'NOTOK', 206


def remove_addon(id):
    logger.debug('deleting plugin {}'.format(id))
    path = os.path.join(DATA_DIR, 'addons', id)
    shutil.rmtree(path)
    global PLUGINS
    for i, p in enumerate(PLUGINS):
        if p.id == id:
            del PLUGINS[i]
            break


def get_items(plugin_id, url, context, PLUGINS, LANGUAGE):
    if 'setproctitle' in sys.modules:
        setproctitle.setproctitle('python TVMLServer ({}:{})'.format(plugin_id, url))
    logger = logging.getLogger(plugin_id)
    logger.debug('Getting items for: {}'.format(url))

    try:
        plugin = [p for p in PLUGINS if p.id == plugin_id][0]
        if not plugin:
            raise Exception('could not load plugin')
        b = bridge()
        b.context = context
        items = plugin.run(b, url, LANGUAGE)
    except:
        logger.exception('Encountered error in plugin: {}'.format(plugin_id))
        items = None
    # logger.debug('get_items finished with {}'.format(items))
    return items


def get_menu(plugin_id, url, PLUGINS, LANGUAGE):
    print('Getting menu for: {}'.format(url))
    url = url.split('?')[1] if '?' in url else url
    try:
        plugin = [p for p in PLUGINS if p.id == id][0]
        if not plugin:
            raise Exception('could not load plugin')
        b = bridge()
        items = plugin.settings(b, url, LANGUAGE)
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
        for r in REPOSITORIES:
            temp = []
            for dir in r['dirs']:
                try:
                    req = requests.get(dir['xml'])
                    link = req.text
                    temp += parse_addon_xml(link, r, dir)
                except:
                    logger.exception('Cannot read repository {}'.format(r['name']))
            for addon in temp:
                try:
                    DB.execute('insert into AVAILABLE_ADDONS values(?,?,?,?,?,?,?,?,?,?)', (addon['id'], r['name'], json.dumps(dir), json.dumps(addon['type']), addon['name'], json.dumps(addon['data']), addon['version'], addon['script'], json.dumps(addon['requires']), addon['icon']))
                except:
                    logger.exception('failed to insert {} into DB'.format(addon))
    logger.debug('Finished refreshing repositories')
    update_addons()
    if e:
        e.set()


@app.route('/installAddon', methods=['POST'])
def installAddon():
    if request.method == 'POST':
        try:
            id = kodi_utils.b64decode(request.form.keys()[0])
            already_installed = [p for p in PLUGINS if p.id == id]
            if already_installed:
                return render_template('alert.xml', title='Already installed',
                                       description="This addon is already installed")
            found = find_addon(id)
            if not found:
                return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
            install_addon(found[0])
            global PLUGINS
            plugin = KodiPlugin(id)
            PLUGINS.append(plugin)
            for r in plugin.requires:
                already_installed = [p for p in PLUGINS if p.id == r]
                if r == 'xbmc.python' or already_installed:
                    continue
                found = find_addon(r)
                if not found:
                    return render_template('alert.xml', title='Unknown addon', description="This addon has a requirement that cannot be found {}".format(r))
                install_addon(found[0])
            return render_template('alert.xml', title='Installation complete',
                                   description="Successfully installed addon {}.\nPlease reload the main screen in order to view the new addon".format(
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
    found = []
    with open_db() as DB:
        for row in DB.execute('select * from AVAILABLE_ADDONS where id=?', (id,)):
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


def install_addon(addon):
    download_url = '{0}/{1}/{1}-{2}.zip'.format(addon['dir']['download'], addon['id'], addon['data']['version'])
    logger.debug('downloading plugin {}'.format(download_url))
    temp = os.path.join(tempfile.gettempdir(), '{}.zip'.format(id))
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


@app.route('/getAddonData', methods=['POST'])
def getAddonData():
    try:
        id = kodi_utils.b64decode(request.form.keys()[0])
        found = find_addon(id)
        if not found:
            return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
        data = found[0]
        return render_template('descriptiveAlert.xml', title=data['name'], _dict=data['data'])
    except:
        logger.exception('Failed to get data on {}'.format(id))
        return render_template('alert.xml', title='Error',
                               description="Failed to get data on addon.\nThis could be due to a network error or bad repository parsing")


@app.route('/viewLog')
def viewLog():
    with open(LOGFILE, 'r') as f:
        log = f.readlines()
        log.reverse()
        return render_template('logTemplate.xml', title='TVMLServer log', text=''.join(log))


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
        name = kodi_utils.b64decode(request.form.keys()[0])
        with open_db() as DB:
            repo_addons = [row for row in DB.execute('select * from AVAILABLE_ADDONS where repo=?', (name,))]
        addons = {}
        for a in repo_addons:
            for type in json.loads(a['type']):
                if not type in addons:
                    addons[type] = []
                addons[type].append(a)

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
            REPOSITORIES.append(repo)
            get_available_addons(REPOSITORIES)
            update_addons()
            return render_template('alert.xml', title='Repository added',
                                   description='Please reload main screen to view additional addons')
    except Exception as e:
        logger.exception('Failed to add repository {}'.format(path))
        return render_template('alert.xml', title='Error', description='{}'.format(e))


last_dir = os.path.expanduser("~")


@app.route('/browse', methods=['POST'])
def browse():
    dir = kodi_utils.b64decode(request.form.keys()[0])
    global last_dir
    if not dir:
        dir = last_dir
    last_dir = dir
    try:
        if os.path.isdir(dir):
            files = [{'url': os.path.join(dir, f), 'title': f} for f in os.listdir('{}'.format(dir))]
            up = os.path.dirname(dir)
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

    db_file = os.path.join(tempfile.gettempdir(), 'TVMLServer.db')
    if os.path.exists(db_file):
        os.remove(db_file)

    global PROCESSES
    PROCESSES = {}

    global PLUGINS
    PLUGINS = manager.list()

    global CONTEXT
    CONTEXT = manager.dict()

    global REPOSITORIES
    REPOSITORIES = [
        {'name': 'Kodi repository', 'dirs': [{'xml': 'http://mirrors.kodi.tv/addons/krypton/addons.xml',
                                              'download': 'http://mirrors.kodi.tv/addons/krypton'}]},
        {'name': 'Kodi Israel', 'dirs': [{'xml': 'https://raw.githubusercontent.com/kodil/kodil/master/addons.xml',
                                          'download': 'https://github.com/kodil/kodil/raw/master/repo'}]},
        {'name': 'Exodus repository',
         'dirs': [{'xml': 'https://offshoregit.com/exodus/addons.xml', 'download': 'https://offshoregit.com/exodus/'}]}
    ]

    with open_db() as DB:
        DB.execute('create table AVAILABLE_ADDONS(id text, repo text, dir text, type text, name text, data text, version text, script text, requires text, icon text)')
        DB.execute('create table PLUGINS(id text primary_key, type text, name text, data text, version text, script text, requires text, icon text, favorite integer)')

    for plugin in os.listdir(os.path.join(DATA_DIR, 'addons')):
        try:
            dir = os.path.join(DATA_DIR, 'addons', plugin)
            if not os.path.isdir(dir):
                continue
            logger.debug('Loading kodi plugin {}'.format(plugin))
            p = KodiPlugin(plugin)
            if not [val for val in p.type if val in ['Video', 'Audio', 'Repository']]:
                logger.debug('Skipping addon {}'.format(p.id))
                continue
            PLUGINS.append(p)
            logger.debug('Successfully loaded plugin: {}'.format(p))
        except Exception as e:
            logger.error('Failed to load kodi plugin {}. Error: {}'.format(plugin, e))
        if plugin.startswith('xbmc.addon.repository'):
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
                    REPOSITORIES.append(repo)
            except:
                logger.exception('Failed to parse installed repository {}'.format(plugin))

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

    # Module multiprocessing is organized differently in Python 3.4+
    try:
        # Python 3.4+
        if sys.platform.startswith('win'):
            import multiprocessing.popen_spawn_win32 as forking
        else:
            import multiprocessing.popen_fork as forking
    except ImportError:
        import multiprocessing.forking as forking

    if sys.platform.startswith('win'):
        # First define a modified version of Popen.
        class _Popen(forking.Popen):
            def __init__(self, *args, **kw):
                if hasattr(sys, 'frozen'):
                    # We have to set original _MEIPASS2 value from sys._MEIPASS
                    # to get --onefile mode working.
                    os.putenv('_MEIPASS2', sys._MEIPASS)
                try:
                    super(_Popen, self).__init__(*args, **kw)
                finally:
                    if hasattr(sys, 'frozen'):
                        # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                        # available. In those cases we cannot delete the variable
                        # but only set it to the empty string. The bootloader
                        # can handle this case.
                        if hasattr(os, 'unsetenv'):
                            os.unsetenv('_MEIPASS2')
                        else:
                            os.putenv('_MEIPASS2', '')


        # Second override 'Popen' class with our modified version.
        forking.Popen = _Popen

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