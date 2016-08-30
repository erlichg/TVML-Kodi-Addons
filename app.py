from __future__ import division
from flask import Flask, render_template, send_from_directory, request
from base64 import b64encode, b64decode
import sys, os, imp, urllib, json, time, traceback
import urlparse
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pywsgi import WSGIServer

reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('scripts')
sys.path.append('plugins')
from Plugin import *
from bridge import bridge

import messages

import threading


class Thread(threading.Thread):
	def __init__(self, target, *args):
		self._target = target
		self._args = args
		self.messages = []
		self.responses = []
		self.stop = False #can be used to indicate stop
		threading.Thread.__init__(self)
	def run(self):
		ans = self._target(*self._args)
		self.message({'type':'end', 'ans':ans})
	def response(self, id, response):
		self.responses.append({'id':id, 'response':response})
	def message(self, msg):
		self.messages.append(msg)



PLUGINS = []
for plugin in os.listdir('plugins'):
	try:
		dir = os.path.join('plugins', plugin)
		if not os.path.isdir(dir):
			continue
		print 'Loading plugin {}'.format(plugin)
		p = Plugin(dir)
		PLUGINS.append(p)
		print 'Successfully loaded plugin: {}'.format(p)
	except Exception as e:
		print 'Failed to load plugin {}. Error: {}'.format(plugin, e)
		



app = Flask(__name__)
app.jinja_env.filters['base64encode'] = b64encode
#app.jinja_env.add_extension('jinja2.ext.do')

_routes = {}

@app.route('/response/<id>')
@app.route('/response/<id>/<res>')
def route(id, res=None):
	handler = _routes.get(id, None)
	if handler is not None:
		return handler(res)
	return render_template('alert.xml', title='Communication error', description="Failed to load page.\nThis could mean the server had a problem, or the request dialog timed-out\nPlease try again")

def add_route(id, handler):
	_routes[id] = handler
	
def remove_route(id):
	del _routes[id]



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


bridges = {}
@app.route('/catalog/<name>')
@app.route('/catalog/<name>/<url>')
@app.route('/catalog/<name>/<url>/<response>')
def catalog(name, url=None, response=None):	
	decoded_url = b64decode(url) if url else ''
	decoded_name = b64decode(name)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.name == decoded_name][0]	
	global bridges
	if response:
		b = bridges[response]
	else:
		b = bridge(__name__, plugin)		
		print 'saving bridge id {}'.format(id(b))
		bridges[str(id(b))] = b
		b.thread = Thread(get_items, b, plugin, decoded_url)
		b.thread.start()
	while b.thread.is_alive():
		if len(b.thread.messages)>0:
			msg = b.thread.messages.pop(0)
			method = getattr(messages, msg['type'])
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))
		time.sleep(0.1)
	#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
	if len(b.thread.messages)>0:
		msg = b.thread.messages.pop(0)
		method = getattr(messages, msg['type'])
		return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))	
	
	raise Exception('Should not get here')

@app.route('/menu/<name>')
@app.route('/menu/<name>/<response>')
def menu(name, response=None):
	decoded_name = b64decode(name)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.name == decoded_name][0]
	global bridges
	if response:
		b = bridges[response]
	else:
		b = bridge(__name__, plugin)		
		print 'saving bridge id {}'.format(id(b))
		bridges[str(id(b))] = b
		b.thread = Thread(get_menu, b, plugin, '')
		b.thread.start()
		
	while b.thread.is_alive():
		if len(b.thread.messages)>0:
			msg = b.thread.messages.pop(0)
			method = getattr(messages, msg['type'])
			return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))
		time.sleep(0.1)
	#Check for possible last message which could have appeared after the thread has died. This could happen if message was sent during time.sleep in while and loop exited immediately afterwards
	if len(b.thread.messages)>0:
		msg = b.thread.messages.pop(0)
		method = getattr(messages, msg['type'])
		return method(plugin, msg, request.url) if response else method(plugin, msg, '{}/{}'.format(request.url, id(b)))


@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main')
def main():	
	return render_template('main.xml', menu=PLUGINS)
	

def get_items(bridge, plugin, url):
	print('Getting items for: {}'.format(url))
	url = url.split('?')[1] if '?' in url else url
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
		items = plugin.menu(bridge, url)
	except:
		print 'Encountered error in plugin: {}'.format(plugin.name)
		traceback.print_exc(file=sys.stdout)
		items = None
	return items

def is_ascii(s):
	return all(ord(c) < 128 for c in s)


		
if __name__ == '__main__':
	http_server = WSGIServer(('',5000), app)
	#http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
