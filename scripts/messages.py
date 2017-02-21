from flask import Flask, render_template, send_from_directory, request
import json
import imageCache
import kodi_utils
import traceback, sys, logging
logger = logging.getLogger('TVMLServer')

import time
import threading

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


def end(plugin, msg, url=None, original_url=None, history=None):
    """Called on plugin end (i.e. when run function returns).
        renders various templates based on items attributes (ans attribute in msg)
    """
    items = msg['ans']
    #print items
    if not items or len(items) == 0:
        logger.debug('end sending 206')
        return {'messagetype':'nothing', 'return_url':url}
    template = None

    for item in items:
        if item.icon:
            if item.icon.startswith('addons'):
                item.icon = '/{}'.format(item.icon)
            elif item.icon.startswith('/'):
                pass
            else:
                item.icon = '/cache/{}'.format(kodi_utils.b64encode(item.icon))
            item.info['poster'] = item.icon
        item.width = 300
        item.height = 300
        imdb = item.info['imdb'] if 'imdb' in item.info else item.info['imdb_id'] if 'imdb_id' in item.info else item.info['imdbnumber'] if 'imdbnumber' in item.info else None
        season = str(item.info['season']) if 'season' in item.info else None
        episode = str(item.info['episode']) if 'episode' in item.info else None
        if imdb:
            # we save in history the imdb id of the movie
            search = imdb;
            if season:
                search += "S" + season;
            if episode:
                search += "E" + episode;
        else:
            # we save in history the original item url
            search = item.url
        if history and search in history:
            item.status = history[search]
    #widths = [item.width for item in items]
    #heights = [item.height for item in items]
    #avg_width = reduce(lambda x, y: x + y, widths) / len(widths)
    #avg_height = reduce(lambda x, y: x + y, heights) / len(heights)
    #for item in items:
    #	item.width = avg_width
    #	item.height = avg_height
    #print items
    doc = render_template("dynamic.xml", menu=items, plugin = plugin)
    return {'doc':doc, 'return_url':url}

def play(plugin, msg, url=None, original_url=None, history=None):
    """Opens the player on msg url attribute"""
    if msg['image']:
        if msg['image'].startswith('addons'):
            msg['image'] = '/{}'.format(msg['image'])
        else:
            msg['image'] = '/cache/{}'.format(kodi_utils.b64encode(msg['image']))
    logger.debug('image after cache = {}'.format(msg['image']))
    imdb = msg['imdb']
    season = msg['season']
    episode = msg['episode']
    if imdb:
        #we save in history the imdb id of the movie
        history = imdb;
        if season:
            history += "S"+season;
        if episode:
            history += "E"+episode;
    else:
        #we save in history the original item url
        history = original_url
    #since url paremeter is the original url that was called which resulted in a play message, we can save this url for time
    #return render_template('player.xml', url=msg['url'], type=msg['playtype'])
    return json.dumps({'messagetype':'play', 'history':history, 'continue': url, 'url': msg['url'], 'stop': msg['stop'], 'type':msg['playtype'], 'imdb':msg['imdb'], 'title':msg['title'], 'description':msg['description'], 'image':msg['image'], 'season':msg['season'], 'episode':msg['episode']})

def isplaying(plugin, msg, url=None, original_url=None, history=None):
    pass


def inputdialog(plugin, msg, url=None, original_url=None, history=None):
    """Shows an input dialog with text field. Returns the response"""
    doc = render_template('inputdialog.xml', title=msg['title'], description=msg['description'], placeholder=msg['placeholder'], button=msg['button'], url=url, msgid=msg['id'], secure=msg['secure'])
    return {'doc':doc,'messagetype':'modal', 'return_url':url}

def alertdialog(plugin, msg, url=None, original_url=None, history=None):
    """Shows an alert dialog"""
    timeout = 5000
    try:
        timeout = int(msg['timeout'])
    except:
        pass
    doc = render_template('alert.xml', title=msg['title'], description=msg['description'], timeout=timeout, url=url, cont=msg['continue'])
    return {'doc': doc, 'return_url':url}

def progressdialog(plugin, msg, url=None, original_url=None, history=None):
    """Shows a progress dialog. Initially with progress 0"""
    logger.debug('returning progress template with {}'.format(msg))
    doc = render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'])
    return {'doc': doc, 'messagetype':'progress', 'return_url':url}


def updateprogressdialog(plugin, msg, url=None, original_url=None, history=None):
    logger.debug('updating progress template with {}'.format(msg))
    doc = render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'])
    return {'doc': doc, 'messagetype':'updateprogress', 'return_url':url}


def selectdialog(plugin, msg, url=None, original_url=None, history=None):
    items = msg['list']
    logger.debug(items)
    if not items or len(items) == 0:
        return {'messagetype':'nothing', 'return_url':url}
    if items[0].title and items[0].subtitle and items[0].icon and items[0].details:
        doc = render_template('list.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url)
        return {'doc': doc, 'messagetype':'modal', 'return_url':url}
    if items[0].title and items[0].icon:
        doc = render_template('grid.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url)
        return {'doc': doc, 'messagetype': 'modal', 'return_url':url}
    doc = render_template('nakedlist.xml', menu=items, title=msg['title'], text = msg['text'].split('\n'), msgid=msg['id'], url=url)
    return {'doc': doc, 'messagetype': 'modal', 'return_url':url}


def closeprogress(plugin, msg, url=None, original_url=None, history=None):
    """Close the progress dialog"""
    logger.debug('close progress message')
    return {'messagetype':'closeprogress', 'return_url':url}

def formdialog(plugin, msg, url=None, original_url=None, history=None):
    #{'type':'formdialog', 'title':title, 'texts':texts, 'buttons':buttons}
    doc = render_template('multiformdialog2.xml', title=msg['title'], sections=msg['sections'], msgid=msg['id'], url=url if msg['cont'] else '')
    return {'doc': doc, 'return_url':url}

def saveSettings(plugin, msg, url=None, original_url=None, history=None):
    logger.debug('SaveSettings in messages')
    msg['url'] = url
    msg['messagetype'] = 'savesettings'
    msg['return_url'] = url
    return msg

def loadSettings(plugin, msg, url=None, original_url=None, history=None):
    logger.debug('loadSettings in messages')
    return {'messagetype':'loadsettings', 'addon':plugin.id, 'msgid':msg['id'], 'url': url , 'return_url':url}

def load(plugin, msg, url=None, original_url=None, history=None):
    msg['cont'] = url
    msg['messagetype'] = 'load'
    msg['return_url'] = url
    return msg
