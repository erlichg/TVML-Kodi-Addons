from __future__ import division
import sys, os, imp, urllib, json, time, traceback, re, getopt, tempfile, AdvancedHTMLParser, urllib2, urlparse, zipfile, shutil, requests, logging, psutil, subprocess
from threading import Timer
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
#import gevent.monkey
#gevent.monkey.patch_all()
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

LANGUAGE='English'

sys.path.append(os.path.join(bundle_dir, 'scripts'))
sys.path.append(os.path.join(bundle_dir, 'scripts', 'kodi'))
sys.path.append(os.path.join(DATA_DIR, 'addons'))

from scripts import kodi_utils
import jinja2
app = Flask(__name__, template_folder=os.path.join(bundle_dir, 'templates'))
app.jinja_env.filters['base64encode'] = kodi_utils.b64encode
#app.jinja_env.add_extension('jinja2.ext.do')
	
import threading

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
		self.message({'type':'end', 'ans':ans})			
		self.onStop()
		self.stop = True
		
	
	def response(self, id, response):
		self.responses.put({'id':id, 'response':response})
		
	def message(self, msg):
		self.messages.put(msg)
	
	def onStop(self):
 		pass
			
def Process(group=None, target=None, name=None, args=(), kwargs={}):	
 	p = MyProcess(group, target, name, args, kwargs)
 	p.messages = multiprocessing.Queue()
	p.responses = multiprocessing.Queue()
	p.stop = False #can be used to indicate stop
	p.id = str(id(p))
	return p


def updateAddons(available, plugins):
	for p in plugins:
		try:
			current_version = p.version
			if not p.id in available:
				continue
			remote_version = available[p.id]['data']['version']
			if version.parse(current_version) < version.parse(remote_version):
				logger.info('Found update for addon {}. Current version: {}, Remote version: {}'.format(p.id, current_version, remote_version))
				install_addon(p.id)
				plugin = KodiPlugin(p.id)
				for i2, p2 in enumerate(plugins):
				 if p2.id == p.id:
				 	del plugins[i2]
				 	plugins.append(plugin)
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
			p.responses.put({'id':id, 'response':res})
			return 'OK', 204
		return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
	else:
		return 'OK', 204

@app.route('/icon.png')
def icon():
	return send_from_directory(bundle_dir, 'icon.png')
	
@app.route('/cache/<id>')
def cache(id):
	file=imageCache.get(id)
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
#@app.route('/catalog/<pluginid>/<url>')
#@app.route('/catalog/<pluginid>/<url>/<process>')
def catalog(pluginid, process=None):
	#try update
	global UPDATE_PROCESS
	if not UPDATE_PROCESS.is_alive():
		UPDATE_PROCESS = multiprocessing.Process(target=updateAddons, args=(AVAILABLE_ADDONS, PLUGINS))
		UPDATE_PROCESS.start()
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
			return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
		
		global PROCESSES
		if process:
			if not process in PROCESSES:
				return render_template('alert.xml', title='Fatal error', description="Failed to load page.\nSomething has gone terribly wrong.\nPlease try to restart the App")
			p = PROCESSES[process]
		else:
			if request.full_path.startswith('/catalog'):
				p = Process(target=get_items, args=(plugin.id, decoded_url, CONTEXT, PLUGINS, LANGUAGE))
			else:
				p = Process(target=get_menu, args=(plugin.id, decoded_url, LANGUAGE))	
			logger.debug('saving process id {}'.format(p.id))	
			PROCESSES[p.id] = p
			def stop():
				time.sleep(5) #close bridge after 5s
				global PROCESSES
				del PROCESSES[p.id]
			#b.thread.onStop = stop
			p.start()
		logger.debug('entering while alive')
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
					#p.join()
					#p.terminate()
					logger.debug('PROCESS {} TERMINATED'.format(p.id))
				return_url = None
				if process:
					#return on same url for more
					return_url = request.url
				else:
					#add response bridge
					return_url = '{}/{}'.format(request.url, p.id)
				#else:
					#No url and no response so add 'fake' url
				#	return_url = '{}/{}/{}'.format(request.url, 'fake', p.id)
				return method(plugin, msg, return_url)
			except:
				traceback.print_exc(file=sys.stdout)
		logger.debug('exiting while alive and entering 5s wait')
		#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
		start = 0
		while start < 5: #wait at most 5 seconds
			try:
				msg = p.messages.get(False)
			except:
				gevent.sleep(0.1)
				start+=0.1
				continue
			try:
				method = getattr(messages, msg['type'])
				if msg['type'] == 'end':				
					global PROCESSES
					del PROCESSES[p.id]
					#p.join()
					#p.terminate()
					logger.debug('PROCESS {} TERMINATED'.format(p.id))
				return method(plugin, msg, request.url) if process else method(plugin, msg, '{}/{}'.format(request.url, p.id))	
			except:
				traceback.print_exc(file=sys.stdout)
		logger.debug('finished 5 sec wait')
		#if we got here, this means thread has probably crashed.
		global PROCESSES
		del PROCESSES[p.id]
		p.join()
		p.terminate()
		logger.error('PROCESS {} CRASHED'.format(p.id))
 		
		return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
	except:
		traceback.print_exc(file=sys.stdout)
		return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")

@app.route('/settings')
@app.route('/settings/<response>')
def settings(response=None):
	global PROCESSES
	if response:
		p = PROCESSES[response]
	else:
		p = Process(target=get_settings)
		logger.debug('saving process id {}'.format(p.id))	
		PROCESSES[p.id] = p
		def stop():
			time.sleep(5) #close bridge after 5s
			global PROCESSES
			del PROCESSES[p.id]
		#b.thread.onStop = stop
		p.start()
	while p.is_alive():
		try:
			msg = p.messages.get(False)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end' or msg['type'] == 'load':
				global PROCESSES
				del PROCESSES[p.id]
				p.join()
				p.terminate()
			return_url = None
			if response:
				#return on same url for more
				return_url = request.url
			else:
				#add response bridge
				return_url = '{}/{}'.format(request.url, p.id)			
			return method(plugin, msg, return_url)
		except:
			gevent.sleep(0.1)
	#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
	while True:
		try:
			msg = p.messages.get(False)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end' or msg['type'] == 'load':
				global PROCESSES
				del PROCESSES[p.id]
				p.join()
				p.terminate()
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, p.id))	
		except:
			time.sleep(0.1)
	raise Exception('Should not get here')
	
@app.route('/subtitles/<msg>')
def subtitles(msg):
	msg = kodi_utils.b64decode(msg)
	logger.debug(msg)


@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main', methods=['POST', 'GET'])
def main():
	favs = []
	if request.method == 'POST':
		try:
			post_data = json.loads(kodi_utils.b64decode(request.form.keys()[0]))
			logger.debug(post_data)
			favs_json = post_data['favs']
			for id in favs_json:
				matching = [p for p in PLUGINS if p.id == id]
				if len(matching) == 0:
					continue #no match found
				if len(matching) == 1:
					favs.append(matching[0])
					continue
				logger.warning('More than one addons found that match id {}'.format())
			favs = [[p for p in PLUGINS if p.id == id][0] for id in favs]
			
			global LANGUAGE
			LANGUAGE = post_data['lang']			
		except:
			pass
	now = time.time()
	while not AVAILABLE_ADDONS and time.time() - now < 30:
		logger.debug('Waiting for repository refresh...')
		time.sleep(1)
	if not AVAILABLE_ADDONS:
		logger.error('Failed to fetch remote repositories. Installing addons may not be available')
	return render_template('main.xml', menu=PLUGINS, favs=favs, url=request.full_path, all=AVAILABLE_ADDONS)
	
@app.route('/removeAddon', methods=['POST'])
def removeAddon():
	try:
		if request.method == 'POST':
			id = kodi_utils.b64decode(request.form.keys()[0])
			logger.debug('deleting plugin {}'.format(id))
			path = os.path.join(DATA_DIR, 'addons', id)
			shutil.rmtree(path)
			global PLUGINS
			for i, p in enumerate(PLUGINS):
				 if p.id == id:
				 	del PLUGINS[i]
				 	break
		return json.dumps({'url':'/main', 'replace':True, 'initial':True}), 212
	except:
		traceback.print_exc(file=sys.stdout)
		return 'NOTOK', 206

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
	#logger.debug('get_items finished with {}'.format(items))
	return items
	
def get_menu(plugin_id, url, LANGUAGE):
	print('Getting menu for: {}'.format(url))
	url = url.split('?')[1] if '?' in url else url
	try:
		plugin = load_plugin(plugin_id)
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
	
def load_plugin(id):
	p = [p for p in PLUGINS if p.id == id][0]
	logger.debug('returning plugin {}'.format(p))
	return p
	for plugin in os.listdir(os.path.join(DATA_DIR, 'addons')):
		if not plugin.startswith('plugin.video.'):
			continue
		try:
			dir = os.path.join(DATA_DIR, 'addons', plugin)
			if not os.path.isdir(dir):
				continue
			logger.debug('Loading kodi plugin {}'.format(plugin))
			p = KodiPlugin(plugin)
			PLUGINS.append(p)
			logger.debug('Successfully loaded plugin: {}'.format(p))
		except Exception as e:
			logger.debug('Failed to load kodi plugin {}. Error: {}'.format(plugin, e))
	logger.error('Failed to find plugin id {}'.format(id))
	return None
	
def getAvailableAddons(REPOSITORIES):
	logger.debug('Refreshing repositories. Please wait...')
	temp = {}
	parser = AdvancedHTMLParser.Parser.AdvancedHTMLParser()
	for r in REPOSITORIES:
		try:
			req = requests.get(r['xml'])
			link = req.text
			parser.feed(link)
			for a in parser.getElementsByTagName('addon'):
				if 'plugin.video.' in a.attributes['id']:
					id = a.attributes['id']
					data = a.attributes
					meta = a.getElementsByAttr('point', 'xbmc.addon.metadata')[0]
					data.update({t.tagName:t.text for t in meta.children})
					if id in temp:
						current_version = temp[id]['data']['version']
						new_version = data['version']
						if version.parse(current_version) >= version.parse(new_version):
							continue
					temp[id] = {'repo':r, 'name':data['name'], 'data':data, 'icon':'/cache/{}'.format(kodi_utils.b64encode('{}/{}/icon.png'.format(r['download'],id)))}
						
		except Exception as e:
			logger.exception('Cannot read repository {} because of {}'.format(r, e))
	#q.put(temp)	
	logger.debug('Finished refreshing repositories')
	return temp
	
@app.route('/installAddon', methods=['POST'])
def installAddon():
	if request.method == 'POST':		
		try:
			id = kodi_utils.b64decode(request.form.keys()[0])
			alreadyInstalled = [p for p in PLUGINS if p.id == id]
			if alreadyInstalled:
				return render_template('alert.xml', title='Already installed', description="This addon is already installed")
			if not id in AVAILABLE_ADDONS:
				return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
			install_addon(id)
			global PLUGINS
			plugin = KodiPlugin(id)
			PLUGINS.append(plugin)
			return render_template('alert.xml', title='Installation complete', description="Successfully installed addon {}.\nPlease reload the main screen in order to view the new addon".format(data['name']))
		except:
			logger.exception('Failed to download/install {}'.format(id))
			return render_template('alert.xml', title='Install error', description="Failed to install addon.\nThis could be due to a network error or bad repository parsing")
	return render_template('alert.xml', title='URL error', description='This URL is invalid')

def install_addon(id):
	data = AVAILABLE_ADDONS[id]
	download_url = '{0}/{1}/{1}-{2}.zip'.format(data['repo']['download'], id, data['data']['version'])
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
	if request.method == 'POST':		
		try:
			id = kodi_utils.b64decode(request.form.keys()[0])
			if not id in AVAILABLE_ADDONS:
				return render_template('alert.xml', title='Unknown addon', description="This addon cannot be found")
			data = AVAILABLE_ADDONS[id]
			return render_template('descriptiveAlert.xml', title=data['name'], _dict=data['data'])
		except:
			logger.exception('Failed to get data on {}'.format(id))
			return render_template('alert.xml', title='Error', description="Failed to get data on addon.\nThis could be due to a network error or bad repository parsing")

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
	#try:
	#	p = psutil.Process(os.getpid())
	#	for handler in p.open_files() + p.connections():
	#		os.close(handler.fd)
	#except Exception, e:
	#	print e
	exe = sys.executable
	subprocess.Popen([exe]+sys.argv)
	#os.execl(python, python, *sys.argv)
	sys.exit(0)


def help(argv):
	print 'Usage: {} [-p <port>] [-d <dir>]'.format(argv[0])
	print
	print '-p <port>, --port=<port>		Run the server on <port>. Default is 5000'
	print '-t <dir>, --temp=<dir>			Specify alternate temp directory. Default is {}'.format(tempfile.gettempdir())
	sys.exit()


def mmain(argv):
	port = 5000 #default
	
	try:
		opts, args = getopt.getopt(argv[1:],"hp:t:",["port=", "temp="])
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

	global PLUGINS
	PLUGINS = manager.list()	
	
	global CONTEXT
	CONTEXT = manager.dict()
	
	global REPOSITORIES
	REPOSITORIES = [
	#{'xml':'http://mirrors.kodi.tv/addons/dharma/addons.xml', 'download':'http://mirrors.kodi.tv/addons/dharma'},
	#{'xml':'http://mirrors.kodi.tv/addons/eden/addons.xml', 'download':'http://mirrors.kodi.tv/addons/eden'},
	#{'xml':'http://mirrors.kodi.tv/addons/frodo/addons.xml', 'download':'http://mirrors.kodi.tv/addons/frodo'},
	#{'xml':'http://mirrors.kodi.tv/addons/gotham/addons.xml', 'download':'http://mirrors.kodi.tv/addons/gotham'},
	#{'xml':'http://mirrors.kodi.tv/addons/helix/addons.xml', 'download':'http://mirrors.kodi.tv/addons/helix'},
	#{'xml':'http://mirrors.kodi.tv/addons/isengard/addons.xml', 'download':'http://mirrors.kodi.tv/addons/isengard'},
	#{'xml':'http://mirrors.kodi.tv/addons/jarvis/addons.xml', 'download':'http://mirrors.kodi.tv/addons/jarvis'},
	{'xml':'http://mirrors.kodi.tv/addons/krypton/addons.xml', 'download':'http://mirrors.kodi.tv/addons/krypton'},
	#{'xml':'https://raw.githubusercontent.com/cubicle-vdo/xbmc-israel/master/addons.xml', 'download':'https://github.com/cubicle-vdo/xbmc-israel/raw/master/repo'},
	{'xml':'https://raw.githubusercontent.com/kodil/kodil/master/addons.xml', 'download':'https://github.com/kodil/kodil/raw/master/repo'},
	{'xml':'https://offshoregit.com/exodus/addons.xml', 'download':'https://offshoregit.com/exodus/'}
	]
				
	
	for plugin in os.listdir(os.path.join(DATA_DIR, 'addons')):
		if not plugin.startswith('plugin.video.'):
			continue
		try:
			dir = os.path.join(DATA_DIR, 'addons', plugin)
			if not os.path.isdir(dir):
				continue
			logger.debug('Loading kodi plugin {}'.format(plugin))
			p = KodiPlugin(plugin)
			PLUGINS.append(p)
			logger.debug('Successfully loaded plugin: {}'.format(p))
		except Exception as e:
			logger.error('Failed to load kodi plugin {}. Error: {}'.format(plugin, e))
	global http_server		
	http_server = WSGIServer(('',port), app)
	import socket
	try:
		addr = socket.gethostbyname(socket.gethostname())
	except:
		addr = socket.gethostname()
			
	
	global AVAILABLE_ADDONS
	#q = multiprocessing.Queue()
	#p = multiprocessing.Process(target=getAvailableAddons, args=(q, REPOSITORIES))
	#p.start()
	#p.join()
	AVAILABLE_ADDONS = getAvailableAddons(REPOSITORIES)
	global UPDATE_PROCESS
	UPDATE_PROCESS = multiprocessing.Process(target=updateAddons, args=(AVAILABLE_ADDONS, PLUGINS))
	UPDATE_PROCESS.start()
	print
	print 'Server now running on port {}'.format(port)
	print 'Connect your TVML client to: http://{}:{}'.format(addr, port)
		#http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	
	#app.run(debug=True, host='0.0.0.0')
		
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
	
	