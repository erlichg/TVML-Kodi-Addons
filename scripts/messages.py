from flask import Flask, render_template, send_from_directory, request
import json
import imageCache
import kodi_utils
import traceback, sys

import time
import threading
import Queue

# utility - spawn a thread to execute target for each args
def run_parallel_in_threads(target, args_list):
	# wrapper to collect return value in a Queue
	def task_wrapper(*args):
		target(*args)
	threads = [threading.Thread(target=task_wrapper, args=(args,)) for args in args_list]
	for t in threads:
		t.start()
	for t in threads:
		t.join()


CACHE=imageCache.imageCache('cache', limit=314572800) #30MB

def end(plugin, msg, url=None):
	"""Called on plugin end (i.e. when run function returns). 
		renders various templates based on items attributes (ans attribute in msg)
	"""
	items = msg['ans']
	print items
	if not items or len(items) == 0:
		return '', 206
	template = None
		
	def work(item):
		if item.icon:
			print 'thread start'
			if item.icon.startswith('kodiplugins') or item.icon.startswith('plugins'):
				item.icon = '/{}'.format(item.icon)
			else:
				item.icon = CACHE.get(item.icon)
			item.info['poster'] = item.icon
			try:
				item.width, item.height = kodi_utils.get_image_size('.{}'.format(item.icon))
				if item.width > 600 or item.height > 600:
					item.width = item.width / 2
					item.height = item.height / 2
				if item.width < 200 or item.height < 200:
					item.width = item.width * 2
					item.height = item.height * 2
			except:
				traceback.print_exc(file=sys.stdout)
				item.width = 300
				item.height = 300
			print 'thread done'
		else:
			item.width = 300
			item.height = 300
		item.context['Item info'] = 'ItemInfo({})'.format(json.dumps(item.info))			
	print 'parallel start'
	run_parallel_in_threads(work, items)
	print 'parallel end'
	for item in items:
		if item.title and item.subtitle and item.icon and item.details and not template:
			template = 'list.xml'
		elif item.title and item.icon and (not item.subtitle or not item.details) and (not template or template == 'list.xml'):
			template = 'grid.xml'
		elif not item.icon and not template:
			template = 'nakedlist.xml'
		else:
			pass		
	print items
	return render_template("dynamic.xml", menu=items, plugin = plugin)

def play(plugin, msg, url=None):
	"""Opens the player on msg url attribute"""
	if msg['image']:
		if msg['image'].startswith('kodiplugins') or msg['image'].startswith('plugins'):
			msg['image'] = '/{}'.format(msg['image'])
		else:
			msg['image'] = CACHE.get(msg['image'])
	print 'image after cache = {}'.format(msg['image'])
	#since url paremeter is the original url that was called which resulted in a play message, we can save this url for time
	#return render_template('player.xml', url=msg['url'], type=msg['playtype'])
	return json.dumps({'continue': url, 'url': msg['url'], 'stop': msg['stop'], 'type':msg['playtype'], 'imdb':msg['imdb'], 'title':msg['title'], 'description':msg['description'], 'image':msg['image'], 'season':msg['season'], 'episode':msg['episode']}), 202
	
def isplaying(plugin, msg, url=None):
	pass


def inputdialog(plugin, msg, url=None):
	"""Shows an input dialog with text field. Returns the response"""
	return render_template('inputdialog.xml', title=msg['title'], description=msg['description'], placeholder=msg['placeholder'], button=msg['button'], url=url, msgid=msg['id'], secure=msg['secure']), 208 #present modal

def alertdialog(plugin, msg, url=None):
	"""Shows an alert dialog"""
	return render_template('alert.xml', title=msg['title'], description=msg['description'])
		
def progressdialog(plugin, msg, url=None):
	"""Shows a progress dialog. Initially with progress 0"""
	print 'returning progress template with {}'.format(msg)
	return render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'])
	
def selectdialog(plugin, msg, url=None):
	items = msg['list']
	print items
	if not items or len(items) == 0:
		return '', 204
	if items[0].title and items[0].subtitle and items[0].icon and items[0].details:
		return render_template('list.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url), 208 #present modal
	if items[0].title and items[0].icon:
		return render_template('grid.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url), 208 #present modal
	return render_template('nakedlist.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url), 208 #present modal


def closeprogress(plugin, msg, url=None):
	"""Close the progress dialog"""
	print 'close progress message'
	return '', 206
	
def formdialog(plugin, msg, url=None):
	#{'type':'formdialog', 'title':title, 'texts':texts, 'buttons':buttons}
	return render_template('multiformdialog2.xml', title=msg['title'], sections=msg['sections'], msgid=msg['id'], url=url if msg['cont'] else '')

def saveSettings(plugin, msg, url=None):
	print 'SaveSettings in messages'	
	return json.dumps(msg), 210
	
def loadSettings(plugin, msg, url=None):
	print 'loadSettings in messages'
	return json.dumps({'type':'loadSettings', 'addon':plugin.id, 'msgid':msg['id'], 'url': url }), 210
	
def load(plugin, msg, url=None):
	return json.dumps(msg), 212
