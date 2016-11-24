from __future__ import division
import sys, os, imp, urllib, json, time, traceback, re
from threading import Timer
try:
	from flask import Flask, render_template, send_from_directory, request
except:
	print 'TVML Server requires flask module.\nPlease install it via "pip install flask"'
	sys.exit(1)
try:
	import setproctitle
except:
	pass

import sqlite3


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
sys.path.append('scripts')
sys.path.append(os.path.join('scripts', 'kodi'))
sys.path.append('plugins')
sys.path.append('kodiplugins')

print sys.executable


import kodi_utils
import jinja2
app = Flask(__name__)
app.jinja_env.filters['base64encode'] = kodi_utils.b64encode
#app.jinja_env.add_extension('jinja2.ext.do')
	
import threading

from Plugin import Plugin, Item
from KodiPlugin import *
from bridge import bridge

import messages



class MyProcess(multiprocessing.Process):
	def run(self):		
		ans = self._target(*self._args, **self._kwargs)		
		print 'Thread adding end message'
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


@app.route('/response/<pid>/<id>', methods=['POST', 'GET'])
@app.route('/response/<pid>/<id>/<res>')
def route(pid, id, res=None):
	if request.method == 'POST':
		res = request.form.keys()[0]
	global PROCESSES
	if pid in PROCESSES:
		p = PROCESSES[pid]
		print 'received response on process {}'.format(pid)
		if p is not None:
			p.responses.put({'id':id, 'response':res})
			return 'OK', 206
		return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")
	else:
		return 'OK', 206

@app.route('/icon.png')
def icon():
	return send_from_directory('.', 'icon.png')
	
@app.route('/plugins/<path:filename>')
def plugin_icon(filename):
	return send_from_directory('plugins', filename)

@app.route('/cache/<path:filename>')
def cache(filename):
	return send_from_directory('cache', filename)
	
@app.route('/kodiplugins/<path:filename>')
def kodiplugin_icon(filename):
	return send_from_directory('kodiplugins', filename)
		
@app.route('/js/<path:filename>')
def js(filename):
	return send_from_directory('js', filename)
	
	
@app.route('/templates/<path:filename>')
def template(filename):
	return send_from_directory('templates', filename)


@app.route('/menu/<pluginid>')
@app.route('/menu/<pluginid>/<process>')
@app.route('/catalog/<pluginid>', methods=['POST', 'GET'])
@app.route('/catalog/<pluginid>/<process>', methods=['POST', 'GET'])
#@app.route('/catalog/<pluginid>/<url>')
#@app.route('/catalog/<pluginid>/<url>/<process>')
def catalog(pluginid, process=None):
	url = None
	if request.method == 'POST':
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
			print 'catalog {}, {}, {}'.format(decoded_id, decoded_url, process)
		else:
			print 'menu {}, {}'.format(decoded_id, process)
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
				sqlite3.connect(':memory:').close()
				p = Process(target=get_items, args=(plugin.id, decoded_url, CONTEXT, PLUGINS))
			else:
				p = Process(target=get_menu, args=(plugin.id, decoded_url))	
			print 'saving process id {}'.format(p.id)		
			PROCESSES[p.id] = p
			def stop():
				time.sleep(5) #close bridge after 5s
				global PROCESSES
				del PROCESSES[p.id]
			#b.thread.onStop = stop
			p.start()
		print 'entering while alive'
		while p.is_alive():
			try:
				msg = p.messages.get(False)
			except:
				gevent.sleep(0.1)
				continue
			try:		
				method = getattr(messages, msg['type'])
				if msg['type'] == 'end' or msg['type'] == 'load':
					global PROCESSES
					del PROCESSES[p.id]
					#p.join()
					#p.terminate()
					print 'PROCESS {} TERMINATED'.format(p.id)
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
		print 'exiting while alive and entering 5s wait'
		#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
		start = 0
		while start < 10: #wait at most 5 seconds
			try:
				msg = p.messages.get(False)
			except:
				gevent.sleep(0.1)
				start+=0.1
				continue
			try:
				method = getattr(messages, msg['type'])
				if msg['type'] == 'end' or msg['type'] == 'load':				
					global PROCESSES
					del PROCESSES[p.id]
					#p.join()
					#p.terminate()
					print 'PROCESS {} TERMINATED'.format(p.id)
				return method(plugin, msg, request.url) if process else method(plugin, msg, '{}/{}'.format(request.url, p.id))	
			except:
				traceback.print_exc(file=sys.stdout)
		print 'finished 5 sec wait'
		#if we got here, this means thread has probably crashed.
		global PROCESSES
		del PROCESSES[p.id]
		p.join()
		p.terminate()
		print 'PROCESS {} CRASHED'.format(p.id)
# 		def restart():
# 			print 'restarting app'
# 			global http_server
# 			http_server.stop()
# 			try:
# 				p = psutil.Process(os.getpid())
# 				for handler in p.get_open_files() + p.connections():
# 					os.close(handler.fd)
# 			except Exception, e:
# 				print e
# 			python = sys.executable
# 			os.execl(python, python, *sys.argv)
# 		Timer(1, restart, ()).start()
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
		print 'saving process id {}'.format(p.id)		
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
	print msg


@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main', methods=['POST', 'GET'])
def main():
	if request.method == 'POST':
		favs = json.loads(kodi_utils.b64decode(request.form.keys()[0]))
		favs = [[p for p in PLUGINS if p.id == id][0] for id in favs]
	else:
		favs = []
	return render_template('main.xml', menu=PLUGINS, favs=favs, url=request.full_path)
	

def get_items(plugin_id, url, context, PLUGINS):
	if 'setproctitle' in sys.modules:
		setproctitle.setproctitle('python TVMLServer ({}:{})'.format(plugin_id, url))
	print('Getting items for: {}'.format(url))	
	
	try:
		plugin = [p for p in PLUGINS if p.id == plugin_id][0]
		if not plugin:
			raise Exception('could not load plugin')
		b = bridge()
		b.context = context
		items = plugin.run(b, url)
	except:
		traceback.print_exc(file=sys.stdout)
		print 'Encountered error in plugin: {}'.format(plugin_id)		
		items = None
	#print 'get_items finished with {}'.format(items)
	return items
	
def get_menu(plugin_id, url):
	print('Getting menu for: {}'.format(url))
	url = url.split('?')[1] if '?' in url else url
	try:
		plugin = load_plugin(plugin_id)
		if not plugin:
			raise Exception('could not load plugin')
		b = bridge()
		items = plugin.settings(b, url)
	except:
		traceback.print_exc(file=sys.stdout)
		print 'Encountered error in plugin: {}'.format(plugin_id)		
		items = None
	return items
	
def get_settings():
	print 'getting settings'
	try:
		b = bridge()
	except:
		traceback.print_exc(file=sys.stdout)
		print 'Encountered error in settings'


def is_ascii(s):
	return all(ord(c) < 128 for c in s)
	
def load_plugin(id):
	p = [p for p in PLUGINS if p.id == id][0]
	print 'returning plugin {}'.format(p)
	return p
	for plugin in os.listdir('plugins'):
		try:
			dir = os.path.join('plugins', plugin)
			if not os.path.isdir(dir):
				continue
			if id == plugin:
				print 'Loading plugin {}'.format(plugin)
				p = Plugin.Plugin(dir)
				print 'Successfully loaded plugin: {}'.format(p)
				return p
		except Exception as e:
			print 'Failed to load plugin {}. Error: {}'.format(plugin, e)
	for plugin in os.listdir('kodiplugins'):
		try:
			dir = os.path.join('kodiplugins', plugin)
			if not os.path.isdir(dir):
				continue
			if id == plugin:
				print 'Loading kodi plugin {}'.format(plugin)
				p = KodiPlugin(dir)
				print 'Successfully loaded kodi plugin: {}'.format(p)
				return p
		except Exception as e:
			print 'Failed to load kodi plugin {}. Error: {}'.format(plugin, e)
	print 'Failed to find plugin id {}'.format(id)
	return None

def mmain():
	manager = multiprocessing.Manager()
	
	global PROCESSES
	PROCESSES = {}

	global PLUGINS
	PLUGINS = manager.list()	
	
	global CONTEXT
	CONTEXT = manager.dict()
	
	for plugin in os.listdir('plugins'):
		try:
			dir = os.path.join('plugins', plugin)
			if not os.path.isdir(dir):
				continue
			print 'Loading plugin {}'.format(plugin)
			p = Plugin.Plugin(dir)
			PLUGINS.append(p)
			print 'Successfully loaded plugin: {}'.format(p)
		except Exception:
			traceback.print_exc(file=sys.stdout)
			print 'Failed to load plugin {}'.format(plugin)
	for plugin in os.listdir('kodiplugins'):
		try:
			dir = os.path.join('kodiplugins', plugin)
			if not os.path.isdir(dir):
				continue
			print 'Loading kodi plugin {}'.format(plugin)
			p = KodiPlugin(dir)
			PLUGINS.append(p)
			print 'Successfully loaded plugin: {}'.format(p)
		except Exception as e:
			print 'Failed to load kodi plugin {}. Error: {}'.format(plugin, e)
	global http_server		
	http_server = WSGIServer(('',5000), app)
	#http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
		
if __name__ == '__main__':
	multiprocessing.freeze_support()			
	mmain()