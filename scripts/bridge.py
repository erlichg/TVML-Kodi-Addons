import importlib, time, sys, json, kodi_utils
import multiprocessing, gevent, logging
logger = logging.getLogger('TVMLServer')



def play_stop(b, _id, stop_completion):
    res = None
    try:
        import setproctitle
        setproctitle.setproctitle('python TVMLServer (play wait {})'.format(_id))
    except:
        pass
    now = time.time()
    while not b.thread.stop and time.time() - now < 18000: #Max wait for 5 hours in case of stuck/aborted app
        try:
            r = b.thread.responses.get(False)
            logger.debug('found response for {}'.format(r['id']))
            if r['id'] == _id:
                logger.debug('received response to {}'.format(_id))
                res = r['response']
                break
            else:
                b.thread.responses.put(r)
        except:
            gevent.sleep(1)
    b.play = None
    if time.time() - now < 18000:
        if res and stop_completion:
            logger.debug('detected player stop at time {}'.format(kodi_utils.b64decode(res)))
            stop_completion(kodi_utils.b64decode(res))
    else:
        logger.debug('forced player stop due to unresponsiveness')
        if stop_completion:
            stop_completion(0)


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
                logger.debug('found response for {}'.format(r['id']))
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

    def _message(self, msg, wait=False, _id=None):
        if not self.thread:
            return None
        if not _id:
            _id = kodi_utils.randomword()
            msg['id'] = '{}/{}'.format(self.thread.id, _id)

        logger.debug('adding message: {}'.format(msg))
        self.thread.message(msg)
        if not wait:
            return
        start = time.time()
        while not self.thread.stop and time.time() - start < 3600: #wait for response at most 1 hour. This is meant to limit amount of threads on web server
            try:
                r = self.thread.responses.get(False)
                logger.debug('found response for {}'.format(r['id']))
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

    def alertdialog(self, title, description, timeout=5000):
        """Show an alert dialog with title and description. Returns immediately"""
        return self._message({'type':'alertdialog', 'title':title, 'description':description, 'timeout':timeout})

    def inputdialog(self, title, description='', placeholder='', button='OK', secure=False):
        """Shows an input dialog to the user with text field. Returns the text the user typed or None if user aborted"""
        s = self._message({'type':'inputdialog', 'title':title, 'description':description, 'placeholder':placeholder, 'button':button, 'secure':secure}, True)
        return kodi_utils.b64decode(s) if s else None

    def progressdialog(self, heading, text=''):
        """Shows a progress dialog to the user"""
        _id = kodi_utils.randomword()
        self.progress = multiprocessing.Process(target=progress_stop, args=(self.thread.responses, self.thread.stop, _id))
        self.progress.title = heading
        self.progress.id = _id
        self.progress.text = text
        #self.progress['process'] = p
        self.progress.daemon = True
        self.progress.start()
        self._message({'type':'progressdialog', 'title':heading, 'text':text, 'value':'0', 'id':'{}/{}'.format(self.thread.id, _id)}, False, _id)

    def updateprogressdialog(self, value, text=None):
        """Updates the progress dialog"""
        try:
            if self.progress and self.progress.is_alive():
                logger.debug('updating progress with {}, {}'.format(value, text))
                return self._message({'type':'updateprogressdialog', 'title':self.progress.title, 'text':text if text else self.progress.text, 'value':value, 'id':'{}/{}'.format(self.thread.id, self.progress.id)}, False, self.progress.id)
        except:
            pass

    def isprogresscanceled(self):
        """Returns whether the progress dialog is still showing or canceled by user"""
        try:
            try:
                self.progress
            except:
                #progress has been closed programatically
                logger.debug('isprogresscanceled True (by script)')
                return True
            if not self.progress.is_alive(): #progress has been cancelled by user
                logger.debug('isprogresscanceled True (by user)')
                return True
            logger.debug('isprogresscanceled False')
            return False
        except:
            logger.exception('isprogresscanceled True (by unknown)')
            return True

    def closeprogress(self):
        """Closes the progress dialog"""
        self._message({'type':'closeprogress'})
        #while self.progress and self.progress['process'].is_alive():
        #	print 'waiting for progress thread'
        #	gevent.sleep(1)
        try:
            self.progress.terminate()
            del self.progress
        except:
            pass
        return None

    def selectdialog(self, title, text='', list_=[]):
        """Shows a selection dialog"""
        ans = self._message({'type':'selectdialog', 'title':title, 'text':text, 'list':list_}, True)
        gevent.sleep(1)
        return ans

    def play(self, url, type_='video', title=None, description=None, image=None, imdb=None, season=None, episode=None, stop_completion=None):
        """Plays a url"""
        logger.debug('Playing {}'.format(url))
        self.play = url
        _id = kodi_utils.randomword()
        try:
            p = multiprocessing.Process(target=play_stop, args=(self, _id, stop_completion))
            p.daemon = True
            p.start()
        except:
            logger.exception('Failed to start play progress process.')
        self._message({'type':'play', 'url':url, 'stop':'/response/{}/{}'.format(self.thread.id, _id), 'playtype': type_, 'title':title, 'description':description, 'image':image, 'imdb':imdb, 'season':season, 'episode':episode})
        return

    def isplaying(self):
        """Returns whether the player is still showing or has been cancelled"""
        return self.play is not None

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
