import importlib, time, sys, json, kodi_utils, sqlite3
import multiprocessing, gevent, logging, thread
logger = logging.getLogger('TVMLServer')


def progress_stop(responses, stop, _id):
    try:
        import setproctitle
        setproctitle.setproctitle('python TVMLServer (progress dialog {})'.format(_id))
    except:
        pass
    now = time.time()
    try:
        while not stop.is_set() and time.time() - now < 300: #Max wait for 5 minutes in case of stuck/aborted app:
            try:
                r = responses.get(False)
                logger.debug('progress_stop found response for {}'.format(r['id']))
                if r['id'] == _id:
                    logger.debug('received progress close')
                    logger.debug('received response to {}'.format(_id))
                    logger.debug('progress closed')
                    break
                else:
                    responses.put(r)
            except:
                gevent.sleep(1)
    except:
        pass
    logger.debug('Progress thread has ended')




class bridge:
    """Bridge class which is created on every client request.
    It is passed to the plugin run method and used to communicate between the plugin and the server.
    For example: pop dialog, request input from user and so on.
    """
    def __init__(self):
        self.thread = multiprocessing.current_process()
        self.listeners = {}
        thread.start_new_thread(self._trigger_monitor, ())

    def _trigger_monitor(self):
        while not self.thread.stop.is_set():
            try:
                t = self.thread.triggers.get(False)
                type = t['type']
                data = t['data']
                logger.debug('{} Got trigger {} with data {} and listeners are {}'.format(self.thread.id, type, data, self.listeners))
                if type in self.listeners:
                    for (id, callback) in self.listeners[type]:
                        logger.debug('Notifying {}'.format(id))
                        try:
                            callback(data)
                        except TypeError:
                            callback()
                        except:
                            logger.exception('Failed to notify listener')
            except:
                gevent.sleep(0.1)
        logger.debug('thread {} trigger monitor has ended'.format(self.thread.id))


    def register_for_trigger(self, type, id, callback):
        logger.debug('{} registering for {}'.format(id, type))
        if not type in self.listeners:
            self.listeners[type] = []
        self.listeners[type].append((id, callback))


    def _message(self, msg, wait=False, _id=None):
        if not self.thread:
            return None
        if not _id:
            _id = kodi_utils.randomword()
            msg['id'] = '{}/{}'.format(self.thread.id, _id)

        logger.debug('Adding message on process {}: {}'.format(self.thread.id, msg))
        self.thread.message(msg)
        if not wait:
            return
        start = time.time()
        while not self.thread.stop.is_set() and time.time() - start < 3600: #wait for response at most 1 hour. This is meant to limit amount of threads on web server
            try:
                r = self.thread.responses.get(False)
                logger.debug('_message found response for {}'.format(r['id']))
                if r['id'] == _id:
                    logger.debug('received response to {}'.format(_id))
                    return r['response']
                else:
                    self.thread.responses.put(r)
            except:
                gevent.sleep(0.1)
        if self.thread.stop:
            logger.debug('finished waiting for response {} due to thread stop'.format(_id))
        else:
            logger.warning('Aborting response wait due to time out')
        return None

    def alertdialog(self, title, description, timeout=5000, cont=False):
        """Show an alert dialog with title and description. Returns immediately"""
        return self._message({'type':'alertdialog', 'title':title, 'description':description, 'timeout':timeout, 'continue':'true' if cont else 'false'})

    def inputdialog(self, title, description='', placeholder='', button='OK', secure=False):
        """Shows an input dialog to the user with text field. Returns the text the user typed or None if user aborted"""
        s = self._message({'type':'inputdialog', 'title':title, 'description':description, 'placeholder':placeholder, 'button':button, 'secure':secure}, True)
        return kodi_utils.b64decode(s) if s else None

    def progressdialog(self, heading, text=''):
        """Shows a progress dialog to the user"""
        _id = kodi_utils.randomword()
        self.progress = {'title': heading, 'id': _id, 'text': text}
        def close():
            del self.progress
        self.register_for_trigger(kodi_utils.TRIGGER_PROGRESS_CLOSE, self.thread.id, close)
        self._message({'type':'progressdialog', 'title':heading, 'text':text, 'value':'0', 'id': self.thread.id}, False, _id)

    def updateprogressdialog(self, value, text=None):
        """Updates the progress dialog"""
        try:
            self.progress
            logger.debug('updating progress with {}, {}'.format(value, text))
            return self._message({'type':'updateprogressdialog', 'title':self.progress['title'], 'text':text if text else self.progress['text'], 'value':value, 'id':self.thread.id}, False, self.progress['id'])
        except:
            pass

    def isprogresscanceled(self):
        """Returns whether the progress dialog is still showing or canceled by user"""
        try:
            self.progress
            logger.debug('isprogresscanceled False')
            return False
        except:
            #progress has been closed programatically
            logger.debug('isprogresscanceled True')
            return True


    def closeprogress(self):
        """Closes the progress dialog"""
        self._message({'type':'closeprogress'})
        try:
            del self.progress
        except:
            pass
        return None

    def selectdialog(self, title, text='', list_=[]):
        """Shows a selection dialog. Returns the index (1 based) of the answer"""
        ans = self._message({'type':'selectdialog', 'title':title, 'text':text, 'list':list_}, True)
        gevent.sleep(1)
        return ans

    def play(self, url, type_='video', title=None, description=None, image=None, imdb=None, season=None, episode=None):
        """
        Playes an item
        :param url: url to play
        :param type_: 'video' or 'audio'
        :param title: item title
        :param description: item description
        :param image: item artwork
        :param imdb: imdb id
        :param season: season number
        :param episode: episode number
        :param stop_completion: callback when item has finished playing. Called with stop time and total time
        :return:
        """
        logger.debug('Playing {}'.format(url))
        _id = kodi_utils.randomword()
        self._message({'type':'play', 'url':url, 'playtype': type_, 'title':title, 'description':description, 'image':image, 'imdb':imdb, 'season':season, 'episode':episode})
        return

    def formdialog(self, title, fields=[], sections={}, cont=False):
        """Show a custom form dialog with custom fields
            A field is an object with a type, a label, a value (initial) and other attributes depending on its type.
            Available types are: textfield, yesno and selection
            textfield:
                displayed as a label. when clicked, user is presented with an input form to modify the field. Additional optional attributes: description, placeholder, button and secure.
            yesno:
                value must be a boolean. displayed as a label with 'Yes' or 'No' depending on the value. Clicking on it changes the value between 'Yes' and 'No'. Has no other attributes.
            selection:
                displayed exactly like yesno, but clicking rotates the field on values from the list. possible values are passed via the 'choices' attribute. Initial value must be one of the choices.

            There are 2 ways you can call this function: With a list of fields passed with the fields parameter, or a dict of sections where key is the title, and value is a list of fields

            cont is a boolean whether to continue receiving messages after form has been dismissed
            returns a dict with keys as field labels and values as their (modified) value
            """
        if fields:
            s = self._message({'type':'formdialog', 'title':title, 'sections':{'General':fields}, 'cont':cont}, True)
        elif sections:
            s = self._message({'type':'formdialog', 'title':title, 'sections':sections, 'cont':cont}, True)
        else:
            raise Exception('Must have either fields or sections')
        return json.loads(kodi_utils.b64decode(s)) if s else None


    def saveSettings(self):
        import xbmcaddon
        for id in xbmcaddon.ADDON_CACHE:
            kodi_utils.set_settings(id, xbmcaddon.ADDON_CACHE[id].settings)