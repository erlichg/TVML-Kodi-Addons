from flask import Flask, render_template
import kodi_utils, globals, KodiPlugin
import logging, urllib, json, urlparse
logger = logging.getLogger('TVMLServer')





def end(plugin, msg, url=None, item_url=None):
    """Called on plugin end (i.e. when run function returns).
        renders various templates based on items attributes (ans attribute in msg)
    """
    items = msg['ans']
    #print items
    if not items or len(items) == 0:
        logger.debug('end sending 206')
        return {'messagetype':'nothing', 'return_url':url}
    template = None
    items = [json.loads(i) for i in items]
    for item in items:
        if item['icon']:
            if item['icon'].startswith('addons'):
                item['icon'] = '/{}'.format(item['icon'])
            elif item['icon'].startswith('/'):
                pass
            else:
                item['icon'] = 'http://{}:{}/?url={}'.format(urlparse.urlparse(url).hostname, globals.PROXY_PORT, kodi_utils.b64encode(item['icon']))
                logger.debug('image after cache = {}'.format(item['icon']))
                #item.icon = '/cache/{}'.format(kodi_utils.b64encode(item.icon))
            item['info']['poster'] = item['icon']
        item['width'] = 300
        item['height'] = 300
        imdb = item['info']['imdb'] if 'imdb' in item['info'] else item['info']['imdb_id'] if 'imdb_id' in item['info'] else item['info']['imdbnumber'] if 'imdbnumber' in item['info'] else None
        season = str(item['info']['season']) if 'season' in item['info'] else None
        episode = str(item['info']['episode']) if 'episode' in item['info'] else None
        if imdb:
            # we save in history the imdb id of the movie
            search = imdb;
            if season:
                search += "S" + season;
            if episode:
                search += "E" + episode;
        else:
            # we save in history the original item url
            search = item['url']
        state = kodi_utils.get_play_history(kodi_utils.b64encode(search))
        try:
            int(state['time'])
            int(state['total'])
            if state['time'] == 0 or state['total'] == 0:
                item['play_state'] = 0  # item hasn't been played
            elif state['time'] * 100 / state['total'] >= 95:
                item['play_state'] = 2  # item has finished playing
            else:
                item['play_state'] = 1  # item is in mid play
        except:
            item['play_state'] = 0  # item hasn't been played

    #widths = [item.width for item in items]
    #heights = [item.height for item in items]
    #avg_width = reduce(lambda x, y: x + y, widths) / len(widths)
    #avg_height = reduce(lambda x, y: x + y, heights) / len(heights)
    #for item in items:
    #	item.width = avg_width
    #	item.height = avg_height
    #print items
    doc = render_template("dynamic.xml", menu=items, plugin = plugin)
    return {'doc':doc, 'return_url':url, 'item_url': item_url}


def play(plugin, msg, url=None, item_url=None):
    """Opens the player on msg url attribute"""
    if msg['image']:
        if msg['image'].startswith('addons'):
            msg['image'] = '/{}'.format(msg['image'])
        else:
            #msg['image'] = '/cache/{}'.format(kodi_utils.b64encode(msg['image']))
            msg['image'] = 'http://{}:{}/?url={}'.format(urlparse.urlparse(url).hostname, globals.PROXY_PORT, kodi_utils.b64encode(msg['image']))
            logger.debug('image after cache = {}'.format(msg['image']))
    if msg['imdb']:
        # we save in history the imdb id of the movie
        search = msg['imdb'];
        if msg['season']:
            search += "S" + msg['season'];
        if msg['episode']:
            search += "E" + msg['episode'];
    else:
        # we save in history the original item url
        search = item_url
    state = kodi_utils.get_play_history(search)
    try:
        int(state['time'])
        int(state['total'])
        if state['time'] == 0 or state['total'] == 0:
            time = 0  # item hasn't been played
        elif state['time'] * 100 / state['total'] >= 95:
            time = 0  # item has finished playing so start at beginning
        else:
            time = state['time']  # item is in mid play
    except:
        time = 0
    ans = {'messagetype':'play', 'stop':'/playstop/{}'.format(search), 'start':'/playstart/{}'.format(search), 'time':time, 'continue': url, 'url': msg['url'], 'type':msg['playtype'], 'imdb':msg['imdb'], 'title':msg['title'], 'description':msg['description'], 'image':msg['image'], 'season':msg['season'], 'episode':msg['episode'], 'return_url':url, 'icon':msg['image']}
    kodi_utils.add_item(plugin['name'], json.dumps(ans))
    #since url paremeter is the original url that was called which resulted in a play message, we can save this url for time
    #return render_template('player.xml', url=msg['url'], type=msg['playtype'])
    return ans


def isplaying(plugin, msg, url=None, item_url=None):
    pass

def inputdialog(plugin, msg, url=None, item_url=None):
    """Shows an input dialog with text field. Returns the response"""
    doc = render_template('inputdialog.xml', title=msg['title'], description=msg['description'], placeholder=msg['placeholder'], button=msg['button'], url=url, msgid=msg['id'], secure=msg['secure'])
    return {'doc':doc,'messagetype':'modal', 'return_url':url, 'item_url':item_url}

def alertdialog(plugin, msg, url=None, item_url=None):
    """Shows an alert dialog"""
    timeout = 5000
    try:
        timeout = int(msg['timeout'])
    except:
        pass
    doc = render_template('alert.xml', title=msg['title'], description=msg['description'], timeout=timeout, url=url, cont=msg['continue'])
    return {'doc': doc, 'return_url':url, 'item_url':item_url}

def progressdialog(plugin, msg, url=None, item_url=None):
    """Shows a progress dialog. Initially with progress 0"""
    logger.debug('returning progress template with {}'.format(msg))
    doc = render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'], data=item_url)
    return {'doc': doc, 'messagetype':'progress', 'return_url':url, 'item_url':item_url, 'stop': '/progressstop/{}'.format(msg['id'])}


def updateprogressdialog(plugin, msg, url=None, item_url=None):
    logger.debug('updating progress template with {}'.format(msg))
    doc = render_template('progressdialog.xml', title=msg['title'], text=msg['text'], value=msg['value'], url=url, msgid=msg['id'], data=item_url)
    return {'doc': doc, 'messagetype':'updateprogress', 'return_url':url, 'item_url':item_url, 'stop': '/progressstop/{}'.format(msg['id'])}


def selectdialog(plugin, msg, url=None, item_url=None):
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
    return {'doc': doc, 'messagetype': 'modal', 'return_url':url, 'item_url':item_url}


def closeprogress(plugin, msg, url=None, item_url=None):
    """Close the progress dialog"""
    logger.debug('close progress message')
    return {'messagetype':'closeprogress', 'return_url':url, 'item_url':item_url}


def formdialog(plugin, msg, url=None, item_url=None):
    #{'type':'formdialog', 'title':title, 'texts':texts, 'buttons':buttons}
    doc = render_template('multiformdialog2.xml', title=msg['title'], sections=msg['sections'], msgid=msg['id'], url=url if msg['cont'] else '')
    return {'doc': doc, 'return_url':url, 'item_url':item_url}


def load(plugin, msg, url=None, item_url=None):
    msg['cont'] = url
    msg['messagetype'] = 'load'
    msg['return_url'] = url
    msg['item_url'] = item_url
    return msg

def refresh(plugin, msg, url=None, item_url=None):
    return {'messagetype':'refresh', 'return_url':url, 'item_url':item_url}