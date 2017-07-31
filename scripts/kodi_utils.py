import base64, random, string, sys, os, logging, json, re, bs4, cgi
from StringIO import StringIO
import struct
from contextlib import contextmanager
import sqlite3, time
import multiprocessing
from globals import PROCESSES, REPOSITORIES, SERVICES

logger = logging.getLogger(__name__)
PROXY_CONFIG='proxy_mode'
LANGUAGE_CONFIG='addon_language'
FAVORITE_CONFIG='favorite_addons'

HISTORY_TABLE='HISTORY'
SETTINGS_TABLE='SETTINGS'
CONFIG_TABLE='CONFIG'
ITEMS_TABLE='ITEMS'

TRIGGER_PLAY_STOP='play stopped'
TRIGGER_SETTINGS_CHANGED='settings changed'
TRIGGER_CONFIG_CHANGED='config changed'
TRIGGER_ABORT='abort'
TRIGGER_PLAY_START='play started'
TRIGGER_PROGRESS_CLOSE='close progress'

DATA_DIR = os.path.join(os.path.expanduser("~"), '.TVMLSERVER')
DB_FILE = os.path.join(DATA_DIR, 'db', 'TVMLServer.db')

def b64decode(data):
	"""Decode base64, padding being optional.

	:param data: Base64 data as an ASCII byte string
	:returns: The decoded byte string.

	"""
	missing_padding = len(data) % 4
	if missing_padding != 0:
		data += b'='* (4 - missing_padding)
	return base64.urlsafe_b64decode(data.encode('utf-8'))
	
def b64encode(s):
	return base64.urlsafe_b64encode(s)

def randomword():
	"""Create a random string of 20 characters"""
	return ''.join(random.choice(string.lowercase) for i in range(20))
	

class UnknownImageFormat(Exception):
    pass

def get_image_size(file_path):
    """
    Return (width, height) for a given img file content - no external
    dependencies except the os and struct modules from core
    """
    size = os.path.getsize(file_path)

    with open(file_path) as input:
        height = -1
        width = -1
        data = input.read(25)

        if (size >= 10) and data[:6] in ('GIF87a', 'GIF89a'):
            # GIFs
            w, h = struct.unpack("<HH", data[6:10])
            width = int(w)
            height = int(h)
        elif ((size >= 24) and data.startswith('\211PNG\r\n\032\n')
              and (data[12:16] == 'IHDR')):
            # PNGs
            w, h = struct.unpack(">LL", data[16:24])
            width = int(w)
            height = int(h)
        elif (size >= 16) and data.startswith('\211PNG\r\n\032\n'):
            # older PNGs?
            w, h = struct.unpack(">LL", data[8:16])
            width = int(w)
            height = int(h)
        elif (size >= 2) and data.startswith('\377\330'):
            # JPEG
            msg = " raised while trying to decode as JPEG."
            input.seek(0)
            input.read(2)
            b = input.read(1)
            try:
                while (b and ord(b) != 0xDA):
                    while (ord(b) != 0xFF): b = input.read(1)
                    while (ord(b) == 0xFF): b = input.read(1)
                    if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
                        input.read(3)
                        h, w = struct.unpack(">HH", input.read(4))
                        break
                    else:
                        input.read(int(struct.unpack(">H", input.read(2))[0])-2)
                    b = input.read(1)
                width = int(w)
                height = int(h)
            except struct.error:
                raise UnknownImageFormat("StructError" + msg)
            except ValueError:
                raise UnknownImageFormat("ValueError" + msg)
            except Exception as e:
                raise UnknownImageFormat(e.__class__.__name__ + msg)
        else:
            raise UnknownImageFormat(
                "Sorry, don't know how to get information from this file."
            )

    return width, height

def windows_pyinstaller_multiprocess_hack():
    # Module multiprocessing is organized differently in Python 3.4+
    try:
        # Python 3.4+
        if sys.platform.startswith('win'):
            import multiprocessing.popen_spawn_win32 as forking
        else:
            import multiprocessing.popen_fork as forking
    except ImportError:
        import multiprocessing.forking as forking

    if sys.platform.startswith('win'):
        # First define a modified version of Popen.
        class _Popen(forking.Popen):
            def __init__(self, *args, **kw):
                if hasattr(sys, 'frozen'):
                    # We have to set original _MEIPASS2 value from sys._MEIPASS
                    # to get --onefile mode working.
                    os.putenv('_MEIPASS2', sys._MEIPASS)
                try:
                    super(_Popen, self).__init__(*args, **kw)
                finally:
                    if hasattr(sys, 'frozen'):
                        # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                        # available. In those cases we cannot delete the variable
                        # but only set it to the empty string. The bootloader
                        # can handle this case.
                        if hasattr(os, 'unsetenv'):
                            os.unsetenv('_MEIPASS2')
                        else:
                            os.putenv('_MEIPASS2', '')

        # Second override 'Popen' class with our modified version.
        forking.Popen = _Popen

@contextmanager
def open_db(file=DB_FILE):
    if not os.path.exists(file):
        open(file, 'w').close()
    for i in range(10):
        try:
            CONN = sqlite3.connect(file)
            break
        except:
            logger.exception('Failed to open DB')
            time.sleep(1)
    if not CONN:
        raise Exception('DB is locked')
    CONN.row_factory = sqlite3.Row
    DB = CONN.cursor()
    yield DB
    CONN.commit()
    DB.close()
    CONN.close()


def get_settings(id):
    try:
        with open_db() as DB:
            DB.execute('select * from SETTINGS where id=?', (id,))
            ans = DB.fetchone()
        if not ans:
            return None
        ans = json.loads(ans['string'])
        return ans
    except:
        logger.exception('Encountered error in get_settings')
        return None

def set_settings(id, settings):
    for i in range(10):
        try:
            settings = json.dumps(settings)
            with open_db() as DB:
                DB.execute('update SETTINGS set string=? where id=?', (settings, id, ))
                if DB.rowcount == 0:
                    DB.execute('insert into SETTINGS values(?,?)', (id, settings, ))
            trigger(TRIGGER_SETTINGS_CHANGED, {'id':id, 'settings':settings})
            break
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to update DB')
            break

def get_config(id, _default=None):
    try:
        with open_db() as DB:
            DB.execute('select * from CONFIG where id=?', (id,))
            ans = DB.fetchone()
        if not ans:
            return _default
        ans = json.loads(ans['string'])
        return ans
    except:
        logger.exception('Encountered error in get_config')
        return _default

def set_config(id, value):
    for i in range(10):
        try:
            value = json.dumps(value)
            with open_db() as DB:
                DB.execute('update CONFIG set string=? where id=?', (value, id, ))
                if DB.rowcount == 0:
                    DB.execute('insert into CONFIG values(?,?)', (id, value, ))
            trigger(TRIGGER_CONFIG_CHANGED, {'id': id, 'value': value})
            break
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to update DB')
            break


def get_play_history(s):
    """
    Gets the play state of the item
    :param s: a unique string describing the movie (i.e. imdb id or direct stream url)
    :return: {'time':time, 'total':total}  where time is last stop time and total is total time of item
    """
    try:
        with open_db() as DB:
            DB.execute('select * from HISTORY where s=?', (s, ))
            ans = DB.fetchone()
        return ans if ans else {'time':0, 'total':0}
    except:
        logger.exception('Failed to retrieve play history')
        return {'time':0, 'total':0}


def set_play_history(s, time, total):
    """
    Sets the state of the item in play history
    :param s: a unique string describing the movie (i.e. imdb id or direct stream url)
    :param time: last stop item
    :param total: total time of item
    :return: None
    """
    time = float(time)
    total = float(total)
    for i in range(10):
        try:
            with open_db() as DB:
                DB.execute('update HISTORY set time=?, total=? where s=?', (time, total, s, ))
                if DB.rowcount == 0:
                    DB.execute('insert into HISTORY values(?,?,?)', (s, time, total, ))
            trigger(TRIGGER_PLAY_STOP, {'time': time, 'total': total})
            break
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to save play history')
            break


def add_item(addon, item):
    decoded_item = json.loads(item)
    to_remove=[]
    with open_db() as DB:
        for row in DB.execute('select rowid,* from ITEMS where addon=?', (addon,)):
            i = json.loads(row['s'])
            if i['url'] == decoded_item['url']:
                to_remove.append(row['rowid'])
    for rowid in to_remove:
        remove_item(rowid)
    for i in range(10):
        try:
            with open_db() as DB:
                DB.execute('insert into ITEMS values(?,?)', (item, addon, ))
            break
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to add item')
            break


def get_items():
    ans = {}
    try:
        with open_db() as DB:
            for row in DB.execute('select * from ITEMS'):
                addon = row['addon']
                if not addon in ans:
                    ans[addon] = []
                ans[addon].append(json.loads(row['s']))
        return ans
    except:
        logger.exception('Failed to retrieve items')


def remove_item(rowid):
    for i in range(10):
        try:
            with open_db() as DB:
                DB.execute('delete from ITEMS where rowid=?', (rowid, ))
            break
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to remove item')
            break

def update_item_stop(stop, time):
    time = float(time)
    for i in range(10):
        to_update = []
        addon = None
        try:
            with open_db() as DB:
                for row in DB.execute('select * from ITEMS'):
                    i = json.loads(row['s'])
                    if i['stop'] == stop:
                        addon = row['addon']
                        i['time'] = time
                        to_update.append(json.dumps(i))
        except sqlite3.OperationalError:
            time.sleep(1)
        except:
            logger.exception('Failed to update item')
            break
    for item in to_update:
        add_item(addon, item)


def trigger(type, data):
    try:
        for p in PROCESSES:
            PROCESSES[p].triggers.put({'type':type, 'data':data})
        for p in SERVICES:
            SERVICES[p].triggers.put({'type':type, 'data':data})
    except:
        logger.exception('Failed to insert trigger')

def trigger_listener_for_settings(id, callback):
    def f(data):
        data = json.loads(data)
        if data['id'] == id:
            try:
                callback(data['settings'])
            except TypeError:
                callback()
            except:
                logger.exception('Failed to notify listener')
    return f

def trigger_listener_for_config(id, callback):
    def f(data):
        data = json.loads(data)
        if data['id'] == id:
            try:
                callback(data['value'])
            except TypeError:
                callback()
            except:
                logger.exception('Failed to notify listener')
    return f

def trigger_listener_for_abort(id, callback):
    def f(data):
        if data == id:
            try:
                callback()
            except:
                logger.exception('Failed to notify listener')
    return f


def tag_conversion(s):
    try:
        s = s.replace('[[', '[').replace(']]', ']')
        s = cgi.escape(s)
        while True:
            m = re.search('(.*)\[B\](.*)\[/B\](.*)', s)
            if m:
                s = '{}<title class="bold">{}</title>{}'.format(m.group(1), m.group(2), m.group(3))
            else:
                break
        while True:
            m = re.search('(.*)\[I\](.*)\[/I\](.*)', s)
            if m:
                s = '{}<title class="italics">{}</title>{}'.format(m.group(1), m.group(2), m.group(3))
            else:
                break
        while True:
            m = re.search('(.*)\[COLOR ([^\]]*)\](.*)\[/COLOR\](.*)', s)
            if m:
                s = '{}<title class="{}">{}</title>{}'.format(m.group(1), m.group(2), m.group(3), m.group(4))
            else:
                break

        #Remove any remaining unknown []
        #m = re.search('(.*)\[[^]]*\](.*)', s)
        #if m:
        #    s = '{}{}'.format(m.group(1), m.group(2))
        #s = s.replace('[', '&#91;').replace(']', '&#93;')
        soup = bs4.BeautifulSoup('<html><body>{}</body></html>'.format(s), 'lxml')

        ans = ''
        for child in soup.find('body').children:
            if type(child) is bs4.element.NavigableString or child.name != 'title':
                ans = ans + '<title class="foo">{}</title>'.format(cgi.escape(child) if type(child) is bs4.element.NavigableString else cgi.escape(child.text))
            elif type(child) is bs4.element.Tag:
                for child2 in child.children:
                    if type(child2) is bs4.element.NavigableString or child2.name != 'title':
                        ans = ans + '<title class="{}">{}</title>'.format(child.attrs['class'][0], cgi.escape(child2) if type(child2) is bs4.element.NavigableString else cgi.escape(child2.text))
                    elif type(child2) is bs4.element.Tag:
                        ans = ans + '<title class="{}">{}</title>'.format('{}'.format('_'.join(sorted(child.attrs['class'][0].split("_") + [child2.attrs['class'][0]]))), cgi.escape(child2.text))

        return ans
    except:
        return '<title class="foo">{}</title>'.format(s)


def column_names(table):
    try:
        with open_db() as DB:
            cursor = DB.execute('select * from {}'.format(table))
            names = list(map(lambda x: x[0], cursor.description))
            return names
    except:
        logger.exception('Failed to get column names of {}'.format(table))
        return []