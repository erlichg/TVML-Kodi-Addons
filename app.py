from __future__ import division
from flask import Flask, render_template, send_from_directory, request

import sys, os, imp, urllib, json, time, traceback, re
import multiprocessing
import urlparse
#import gevent.monkey
#gevent.monkey.patch_all()
from gevent.pywsgi import WSGIServer

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('scripts')
sys.path.append(os.path.join('scripts', 'kodi'))
sys.path.append('plugins')
sys.path.append('kodiplugins')

import utils
app = Flask(__name__)
app.jinja_env.filters['base64encode'] = utils.b64encode
#app.jinja_env.add_extension('jinja2.ext.do')
	
import threading

from Plugin import Plugin, Item
from KodiPlugin import *
from bridge import bridge

import messages


bridges = {}

PLUGINS = []
for plugin in os.listdir('plugins'):
	try:
		dir = os.path.join('plugins', plugin)
		if not os.path.isdir(dir):
			continue
		print 'Loading plugin {}'.format(plugin)
		p = Plugin.Plugin(dir)
		PLUGINS.append(p)
		print 'Successfully loaded plugin: {}'.format(p)
	except Exception as e:
		print 'Failed to load plugin {}. Error: {}'.format(plugin, e)
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
			
class Process(multiprocessing.Process):
	def run(self):
		self.messages = multiprocessing.Queue()
		self.responses = multiprocessing.Queue()
		self.stop = False #can be used to indicate stop
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
		
# def Process(group=None, target=None, name=None, args=(), kwargs={}):
# 	ans = multiprocessing.Queue()
# 	args = (ans,)+args
# 	p = multiprocessing.Process(group, target, name, args, kwargs)
# 	p.messages = multiprocessing.Queue()
# 	p.responses = multiprocessing.Queue()
# 	p.stop = False #can be used to indicate stop
# 	
# 	orig_run = p.run
# 	
# 	def run():
# 		orig_run()		
# 		print 'Thread adding end message'
# 		try:
# 			ans2 = ans.get(True, 5)
# 		except:
# 			ans2 = None
# 		p.message({'type':'end', 'ans':ans2})		
# 		p.onStop()
# 		p.stop = True
# 	p.run = run
# 	def response(id, response):
# 		p.responses.put({'id':id, 'response':response})
# 	p.response = response
# 	
# 	def message(msg):
# 		p.messages.put(msg)
# 	p.message = message
# 	
#  	def onStop():
#  		pass
#  	p.onStop = onStop
# 	
# 	return p



@app.route('/response/<bridge>/<id>', methods=['POST', 'GET'])
@app.route('/response/<bridge>/<id>/<res>')
def route(bridge, id, res=None):
	if request.method == 'POST':
		res = request.form.keys()[0]
	global bridges
	b = bridges[bridge]
	if b is not None:
		b.thread.responses.put({'id':id, 'response':res})
		return 'OK', 206
	return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")

@app.route('/icon.png')
def icon():
	return send_from_directory('.', 'icon.png')
	
@app.route('/plugins/<path:filename>')
def plugin_icon(filename):
	return send_from_directory('plugins', filename)
	
@app.route('/kodiplugins/<path:filename>')
def kodiplugin_icon(filename):
	return send_from_directory('kodiplugins', filename)
		
@app.route('/js/<path:filename>')
def js(filename):
	return send_from_directory('js', filename)
	
	
@app.route('/templates/<path:filename>')
def template(filename):
	return send_from_directory('templates', filename)



@app.route('/catalog/<pluginid>')
@app.route('/catalog/<pluginid>/<url>')
@app.route('/catalog/<pluginid>/<url>/<response>')
def catalog(pluginid, url=None, response=None):
	if not url:
		decoded_url = ''
	elif url == 'fake':
		decoded_url = ''
	else:
		decoded_url = utils.b64decode(url)
	decoded_id = utils.b64decode(pluginid)
	print 'catalog {}, {}, {}'.format(decoded_id, decoded_url, response)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.id == decoded_id][0]	
	global bridges
	if response:
		b = bridges[response]
	else:
		b = bridge(__name__, plugin)		
		print 'saving bridge id {}'.format(id(b))
		bridges[str(id(b))] = b
		#b.thread = Thread(get_items, b, plugin, decoded_url)
		b.thread = Process(target=get_items, args=(b, plugin, decoded_url))
		def stop():
			time.sleep(5) #close bridge after 10s
			global bridges
			print 'brfore stop {}'.format(bridges)
			del bridges[str(id(b))]
			print 'after stop {}'.format(bridges)
		#b.thread.onStop = stop
		b.thread.start()
	while b.thread.is_alive():
		try:
			msg = b.thread.messages.get(False)
			print 'got message {}'.format(msg)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end':
				global bridges
				del bridges[str(id(b))]
				b.thread.join()
				b.thread.terminate()
			return_url = None
			if response:
				#return on same url for more
				return_url = request.url
			elif url:
				#add response bridge
				return_url = '{}/{}'.format(request.url, id(b))
			else:
				#No url and no response so add 'fake' url
				return_url = '{}/{}/{}'.format(request.url, 'fake', id(b))
			return method(plugin, msg, return_url)
		except:
			time.sleep(0.1)
	#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
	while True:
		try:
			msg = b.thread.messages.get(False)
			print 'got message {}'.format(msg)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end':
				global bridges
				del bridges[str(id(b))]
				b.thread.join()
				b.thread.terminate()
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))	
		except:
			time.sleep(0.1)
	raise Exception('Should not get here')

@app.route('/menu/<pluginid>')
@app.route('/menu/<pluginid>/<response>')
def menu(pluginid, response=None):
	decoded_id = utils.b64decode(pluginid)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.id == decoded_id][0]
	global bridges
	if response:
		b = bridges[response]
	else:
		b = bridge(__name__, plugin)		
		print 'saving bridge id {}'.format(id(b))
		bridges[str(id(b))] = b
		b.thread = Process(target=get_menu, args=(b, plugin, ''))
		def stop():
			time.sleep(5)
			global bridges
			print 'brfore stop {}'.format(bridges)
			del bridges[str(id(b))]
			print 'after stop {}'.format(bridges)
		#b.thread.onStop = stop
		b.thread.start()
		
	while b.thread.is_alive():
		try:
			msg = b.thread.messages.get(False)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end':
				global bridges
				del bridges[str(id(b))]
				b.thread.join()
				b.thread.terminate()
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))
		except:
			time.sleep(0.1)
	#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards	
	while True:
		try:
			msg = b.thread.messages.get(False)
			method = getattr(messages, msg['type'])
			if msg['type'] == 'end':
				global bridges
				del bridges[str(id(b))]
				b.thread.join()
				b.thread.terminate()
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))
		except:
			time.sleep(0.1)
	raise Exception('Should not get here')

@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main')
def main():
	return render_template('main.xml', menu=PLUGINS)
	

def get_items(bridge, plugin, url):
	print('Getting items for: {}'.format(url))
	try:
		items = plugin.run(bridge, url)
	except:
		print 'Encountered error in plugin: {}'.format(plugin.name)
		traceback.print_exc(file=sys.stdout)
		items = None
	return items
	
def get_menu(bridge, plugin, url):
	print('Getting menu for: {}'.format(url))
	url = url.split('?')[1] if '?' in url else url
	try:
		items = plugin.settings(bridge, url)
	except:
		print 'Encountered error in plugin: {}'.format(plugin.name)
		traceback.print_exc(file=sys.stdout)
		items = None
	return items

def is_ascii(s):
	return all(ord(c) < 128 for c in s)

def mmain():
	http_server = WSGIServer(('',5000), app)
	#http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
		
if __name__ == '__main__':
				
	mmain()