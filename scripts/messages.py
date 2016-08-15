from flask import Flask, render_template, send_from_directory, request
import json

def end(plugin, msg, url=None):
	"""Called on plugin end (i.e. when run function returns). 
		renders various templates based on items attributes (ans attribute in msg)
	"""
	items = msg['ans']
	print items
	if not items or len(items) == 0:
		return '', 206
	if items[0].title and items[0].subtitle and items[0].icon and items[0].details:
		return render_template('list.xml', menu=items, plugin=plugin)
	if items[0].title and items[0].icon:
		return render_template('grid.xml', menu=items, plugin=plugin)	
	return render_template('nakedlist.xml', menu=items, plugin = plugin)

def play(plugin, msg, url=None):
	"""Opens the player on msg url attribute"""
	return json.dumps({'url': msg['url'], 'stop': msg['stop'], 'type':msg['playtype']}), 202
	
def isplaying(plugin, msg, url=None):
	pass


def inputdialog(plugin, msg, url=None):
	"""Shows an input dialog with text field. Returns the response"""
	return render_template('inputdialog.xml', title=msg['title'], description=msg['description'], placeholder=msg['placeholder'], button=msg['button'], url=url, msgid=msg['id'])

def alertdialog(plugin, msg, url=None):
	"""Shows an alert dialog"""
	return render_template('alert.xml', title=msg['title'], description=msg['description'])
		
def progressdialog(plugin, msg, url=None):
	"""Shows a progress dialog. Initially with progress 0"""
	return render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'])
	
def selectdialog(plugin, msg, url=None):
	items = msg['list']
	print items
	if not items or len(items) == 0:
		return '', 204
	if items[0].title and items[0].subtitle and items[0].icon and items[0].details:
		return render_template('list.xml', menu=items, msgid=msg['id'], url=url)
	if items[0].title and items[0].icon:
		return render_template('grid.xml', menu=items, msgid=msg['id'], url=url)	
	return render_template('nakedlist.xml', menu=items, msgid=msg['id'], url=url)


def closeprogress(plugin, msg, url=None):
	"""Close the progress dialog"""
	return '', 206
	
	