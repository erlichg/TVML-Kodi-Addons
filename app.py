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
sys.path.append(os.path.join('scripts', 'kodi'))
sys.path.append('plugins')
from Plugin import Plugin

PLUGINS = []
for plugin in os.listdir('plugins'):
	try:
		print 'Loading plugin {}'.format(plugin)
		p = Plugin(__name__, os.path.join('plugins', plugin))
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
	if len(items) == 0:
		if not isplaying():
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

def inputdialog(title):
	return message({'type':'inputdialog', 'title':title, 'description':'blah blah blah'})
	
def progressdialog(heading, line1='', line2='', line3=''):
	return message({'type':'progressdialog', 'title':heading, 'line1':line1, 'line2':line2, 'line3':line3})
	
def updateprogressdialog(percent, line1='', line2='', line3=''):
	print 'updating progress with {}, {}, {}, {}'.format(percent, line1, line2, line3)
	return message({'type': 'updateprogress', 'percent':percent, 'line1':line1, 'line2':line2, 'line3':line3})

def isprogresscanceled():
	return message({'type':'isprogresscanceled'}) in ['true', 'True', True]

def closeprogress():
	return message({'type':'closeprogress'})
	
def selectdialog(title, list_):
	return message({'type':'selectdialog', 'title':title, 'list':list_})
	
def play(url):
	print 'Playing {}'.format(url)
	return message({'type':'play', 'url':url})

def isplaying():
	return message({'type':'isplaying'}) in ['true', 'True', True]
	   
if __name__ == '__main__':
	http_server = WSGIServer(('',5000), app)
	http_server.log = open('http.log', 'w')
	http_server.serve_forever()
	#app.run(debug=True, host='0.0.0.0')
