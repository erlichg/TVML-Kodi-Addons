import base64, random, string, sys, os, logging, json
from StringIO import StringIO
import struct
from contextlib import contextmanager
import sqlite3, time

logger = logging.getLogger(__name__)

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
def open_db():
    global DB_FILE
    if not os.path.exists(DB_FILE):
        open(DB_FILE, 'w').close()
    for i in range(10):
        try:
            CONN = sqlite3.connect(DB_FILE)
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
    try:
        settings = json.dumps(settings)
        with open_db() as DB:
            DB.execute('update SETTINGS set string=? where id=?', (settings, id, ))
            if DB.rowcount == 0:
                DB.execute('insert into SETTINGS values(?,?)', (id, settings, ))
    except:
        logger.exception('Failed to update DB')

def get_config(id):
    try:
        with open_db() as DB:
            DB.execute('select * from CONFIG where id=?', (id,))
            ans = DB.fetchone()
        if not ans:
            return None
        ans = json.loads(ans['string'])
        return ans
    except:
        logger.exception('Encountered error in get_config')
        return None

def set_config(id, value):
    try:
        value = json.dumps(value)
        with open_db() as DB:
            DB.execute('update CONFIG set string=? where id=?', (value, id, ))
            if DB.rowcount == 0:
                DB.execute('insert into CONFIG values(?,?)', (id, value, ))
    except:
        logger.exception('Failed to update DB')


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
    try:
        with open_db() as DB:
            DB.execute('update HISTORY set time=?, total=? where s=?', (time, total, s, ))
            if DB.rowcount == 0:
                DB.execute('insert into HISTORY values(?,?,?)', (s, time, total, ))
    except:
        logger.exception('Failed to save play history')