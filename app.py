from __future__ import division
from flask import Flask, render_template, send_from_directory, request
from base64 import b64encode, b64decode
import sys, os, imp, urllib, json, time
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
bridge = bridge(__name__)

import threading


class Thread(threading.Thread):
	def __init__(self, target, *args):
		self._target = target
		self._args = args
		self.messages = []
		self.responses = []
		self.id = 0
		threading.Thread.__init__(self)
	def run(self):
		ans = self._target(*self._args)
		self.message({'type':'end', 'ans':ans})
	def response(self, id, response):
		self.responses.append({'id':id, 'response':response})
	def message(self, msg):
		msg['id'] = self.id
		self.id+=1
		self.messages.append(msg)



PLUGINS = []
for plugin in os.listdir('plugins'):
	try:
		print 'Loading plugin {}'.format(plugin)
		p = Plugin(bridge, os.path.join('plugins', plugin))
		PLUGINS.append(p)
		print 'Successfully loaded plugin: {}'.format(p)
	except Exception as e:
		print 'Failed to load plugin {}. Error: {}'.format(plugin, e)



app = Flask(__name__)
app.jinja_env.filters['base64encode'] = b64encode

@app.route('/icon.png')
def icon():
	return send_from_directory('.', 'icon.png')
	
@app.route('/plugins/<path:filename>')
def plugin_icon(filename):
	return send_from_directory('plugins', filename)
		
@app.route('/js/<path:filename>')
def js(filename):
	return send_from_directory('js', filename)
	
@app.route('/templates/<path:filename>')
def template(filename):
	return send_from_directory('templates', filename)

thread = None
@app.route('/catalog/<name>')
@app.route('/catalog/<name>/<url>')
def catalog(name, url=None):	
	url = b64decode(url) if url else ''
	name = b64decode(name)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.name == name][0]
	global thread
	thread = Thread(get_items, plugin, url)
	thread.start()
	while thread.is_alive():
		if len(thread.messages)>0:
			msg = thread.messages.pop(0)
			return decipher_message(plugin, msg)
		time.sleep(0.1)
	if len(thread.messages)>0:
		msg = thread.messages.pop(0)
		return decipher_message(plugin, msg)		
	
	print 'Should not get here'

def decipher_message(plugin, msg):
	print 'deciphering {}'.format(msg)
	if msg['type'] == 'end':
		items = msg['ans']
		print items
		if not items or len(items) == 0:
			if not bridge.isplaying():
				return render_template('alert.xml')
			return '', 204
		if items[0].title and items[0].subtitle and items[0].icon and items[0].details:
			return render_template('list.xml', menu=items, plugin=plugin)
		if items[0].title and items[0].icon:
			return render_template('grid.xml', menu=items, plugin=plugin)	
		return render_template('nakedlist.xml', menu=items, plugin = plugin)
	if msg['type'] == 'play':
		return msg['url'], 202
	if msg['type'] == 'inputdialog':
		return render_template('inputdialog.xml', title=msg['title'], description=msg['description'], placeholder=msg['placeholder'], button=msg['button'])


@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main')
def main():	
	return render_template('main.xml', menu=PLUGINS)
	


@app.route('/response/<id>/<response>')
def response(id, response):
	global thread
	thread.responses.append({'id':id, 'response':response})
	return 'OK', 205

def get_items(plugin, url):
	print('Getting items for: {}'.format(url))
	url = url.split('?')[1] if '?' in url else url	
	items = plugin.run(url)
	return items

def is_ascii(s):
	return all(ord(c) < 128 for c in s)

id=0
def message(msg):
	global thread
	if not thread:
		return None
	print 'adding message: {}'.format(msg)
	thread.message(msg)
	while True:
		for r in thread.responses:
			if r['id'] == str(msg['id']):
				thread.responses.remove(r)
				return r['response']
		time.sleep(0.1)
		
if __name__ == '__main__':
	http_server = WSGIServer(('',5000), app)
	http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
