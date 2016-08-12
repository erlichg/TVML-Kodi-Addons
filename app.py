from __future__ import division
from flask import Flask, render_template, send_from_directory, request
from base64 import b64encode, b64decode
import sys, os, imp, urllib, json, time
import urlparse
import gevent.monkey
from bridge import bridge
bridge = bridge(__name__)
gevent.monkey.patch_all()
from gevent.pywsgi import WSGIServer


reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('scripts')
sys.path.append(os.path.join('scripts', 'kodi'))
sys.path.append('plugins')
from Plugin import Plugin

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

@app.route('/catalog/<name>')
@app.route('/catalog/<name>/<url>')
def catalog(name, url=None):	
	url = b64decode(url) if url else ''
	name = b64decode(name)
	#current_item = get_items('')[int(id)]
	plugin = [p for p in PLUGINS if p.name == name][0]
	print 'found plugin {}'.format(plugin)
	items = get_items(plugin, url)
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

@app.route('/helloworld')
def helloworld():
	return render_template('helloworld.xml')

@app.route('/main')
def main():	
	return render_template('main.xml', menu=PLUGINS)
	
event_list = []
@app.route('/events')
def events():
	global event_list
	if len(event_list)>0:
		return json.dumps(event_list.pop(0)), 203
	else:
		return '', 204

response_list = []	
@app.route('/response/<id>/<response>')
def response(id, response):
	global response_list
	response_list.append({'id':id, 'response':response})
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
	global id
	msg['id'] = id
	id+=1
	global event_list
	event_list.append(msg)
	global response_list
	while True:
		for r in response_list:
			if r['id'] == str(msg['id']):
				response_list.remove(r)
				return r['response']
		time.sleep(0.1)

	   
if __name__ == '__main__':
	http_server = WSGIServer(('',5000), app)
	http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
