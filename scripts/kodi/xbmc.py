## @package xbmc
#  Various classes and functions to interact with XBMC.
#
"""
Various classes and functions to interact with Kodi.
"""

import xbmcgui as _xbmcgui
import xbmcplugin as _xbmcplugin
import xbmcaddon as _xbmcaddon
import time, re, os, sys, tempfile, logging, zipfile
logger = logging.getLogger('TVMLServer')
import kodi_utils
import random
if getattr(sys, 'frozen', False):
	# we are running in a bundle
	bundle_dir = sys._MEIPASS
else:
	bundle_dir = '.'

CAPTURE_FLAG_CONTINUOUS = 1
CAPTURE_FLAG_IMMEDIATELY = 2
CAPTURE_STATE_DONE = 3
CAPTURE_STATE_FAILED = 4
CAPTURE_STATE_WORKING = 0
DRIVE_NOT_READY = 1
ENGLISH_NAME = 2
ISO_639_1 = 0
ISO_639_2 = 1
LOGDEBUG = 0
LOGERROR = 4
LOGFATAL = 6
LOGINFO = 1
LOGNONE = 7
LOGNOTICE = 2
LOGSEVERE = 5
LOGWARNING = 3
PLAYER_CORE_AUTO = 0
PLAYER_CORE_DVDPLAYER = 1
PLAYER_CORE_MPLAYER = 2
PLAYER_CORE_PAPLAYER = 3
PLAYLIST_MUSIC = 0
PLAYLIST_VIDEO = 1
SERVER_AIRPLAYSERVER = 2
SERVER_EVENTSERVER = 6
SERVER_JSONRPCSERVER = 3
SERVER_UPNPRENDERER = 4
SERVER_UPNPSERVER = 5
SERVER_WEBSERVER = 1
SERVER_ZEROCONF = 7
TRAY_CLOSED_MEDIA_PRESENT = 96
TRAY_CLOSED_NO_MEDIA = 64
TRAY_OPEN = 16
__author__ = 'Team Kodi <http://kodi.tv>'
__credits__ = 'Team Kodi'
__date__ = 'Fri May 01 16:22:03 BST 2015'
__platform__ = 'ALL'
__version__ = '2.20.0'
abortRequested = False
bridge=None
LANGUAGE=None


"""Returns ``True`` if Kodi prepares to close itself"""


class Keyboard(object):
	"""
	Creates a new Keyboard object with default text heading and hidden input flag if supplied.

	:param line: string - default text entry.
	:param heading: string - keyboard heading.
	:param hidden: boolean - True for hidden text entry.

	Example::

		kb = xbmc.Keyboard('default', 'heading', True)
		kb.setDefault('password') # optional
		kb.setHeading('Enter password') # optional
		kb.setHiddenInput(True) # optional
		kb.doModal()
		if (kb.isConfirmed()):
			text = kb.getText()
	"""
	def __init__(self, line='', heading='', hidden=False):
		"""
		Creates a new Keyboard object with default text heading and hidden input flag if supplied.

		line: string - default text entry.
		heading: string - keyboard heading.
		hidden: boolean - True for hidden text entry.

		Example:
			kb = xbmc.Keyboard('default', 'heading', True)
			kb.setDefault('password') # optional
			kb.setHeading('Enter password') # optional
			kb.setHiddenInput(True) # optional
			kb.doModal()
			if (kb.isConfirmed()):
				text = kb.getText()
		"""
		logger.debug('init keyboard')
		self.ans = None
		self.line = line
		self.placeholder=''	
		self.heading = heading
		self.hidden = hidden

	def doModal(self, autoclose=0):
		"""Show keyboard and wait for user action.

		:param autoclose: integer - milliseconds to autoclose dialog.

		.. note::
			autoclose = 0 - This disables autoclose

		Example::

			kb.doModal(30000)
		"""
		logger.debug('Showing inputdialog')
		self.ans = bridge.inputdialog(self.heading, description=self.line, placeholder=self.placeholder, secure=self.hidden)

	def setDefault(self, line=''):
		"""Set the default text entry.

		:param line: string - default text entry.

		Example::

			kb.setDefault('password')
		"""
		self.placeholder = line

	def setHiddenInput(self, hidden=False):
		"""Allows hidden text entry.

		:param hidden: boolean - ``True`` for hidden text entry.

		Example::

			kb.setHiddenInput(True)
		"""
		self.hidden = hidden

	def setHeading(self, heading):
		"""Set the keyboard heading.

		:param heading: string - keyboard heading.

		Example::

			kb.setHeading('Enter password')
		"""
		self.heading = heading

	def getText(self):
		"""Returns the user input as a string.

		:return: entered text

		.. note::
			This will always return the text entry even if you cancel the keyboard.
			Use the isConfirmed() method to check if user cancelled the keyboard.
		"""
		return self.ans

	def isConfirmed(self):
		"""Returns ``False`` if the user cancelled the input.

		:return: confirmed status

		example::

			if (kb.isConfirmed()):
				pass
		"""
		return self.ans


class Player(object):
	"""
	Player()

	Creates a new Player with as default the xbmc music playlist.

	.. note:: currently Player class constructor does not take any parameters.
		Kodi automatically selects a necessary player.
	"""
	def __init__(self):
		"""
		Creates a new Player with as default the xbmc music playlist.
		"""
		self.is_playing = False
		self.time = 0
		self.total = -1
		def play_start():
			self.is_playing = True
			self.onPlayBackStarted()
		bridge.register_for_trigger(kodi_utils.TRIGGER_PLAY_START, bridge.thread.id, play_start)

		def play_stop(history):
			logger.debug('stop play is detected')
			self.is_playing = False
			self.time = history['time']
			self.total = history['total']
			if history['time'] == history['total']:
				self.onPlayBackEnded()
			else:
				self.onPlayBackStopped()

		bridge.register_for_trigger(kodi_utils.TRIGGER_PLAY_STOP, bridge.thread.id, play_stop)

	def play(self, item=None, listitem=None, windowed=False, statrpos=-1):
		"""
		Play this item.

		:param item: [opt] string - filename, url or playlist.
		:param listitem: [opt] listitem - used with setInfo() to set different infolabels.
		:param windowed: [opt] bool - true=play video windowed, false=play users preference.(default)
		:param startpos: [opt] int - starting position when playing a playlist. Default = -1

		.. note:: If item is not given then the Player will try to play the current item
			in the current playlist.

		You can use the above as keywords for arguments and skip certain optional arguments.
		Once you use a keyword, all following arguments require the keyword.

		example::

			listitem = xbmcgui.ListItem('Ironman')
			listitem.setInfo('video', {'Title': 'Ironman', 'Genre': 'Science Fiction'})
			xbmc.Player().play(url, listitem, windowed)
			xbmc.Player().play(playlist, listitem, windowed, startpos)
		"""
		logger.debug('called Player.play with item={}, listitem={}'.format(item, listitem))
		if listitem:
			_xbmcplugin.setResolvedUrl(0, True, listitem)
		url=None
		if item.startswith('plugin://'):
			executebuiltin('RunPlugin({})'.format(item))
			#m = re.search('plugin://([^/]*)/(.*)', item)
			#if m:
			#	url = m.group(2)
			#	bridge.play(url=url)
			#else:
			#	logger.error('Got bad play url {}'.format(item))
		else:
			url=item
			bridge.play(url=url)

	def stop(self):
		"""Stop playing."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def pause(self):
		"""Pause playing."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def playnext(self):
		"""Play next item in playlist."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def playprevious(self):
		"""Play previous item in playlist."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def playselected(self, selected):
		"""Play a certain item from the current playlist."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onPlayBackStarted(self):
		"""Will be called when xbmc starts playing a file."""
		pass

	def onPlayBackEnded(self):
		"""Will be called when xbmc stops playing a file."""
		pass

	def onPlayBackStopped(self):
		"""Will be called when user stops xbmc playing a file."""
		pass

	def onPlayBackPaused(self):
		"""Will be called when user pauses a playing file."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onPlayBackResumed(self):
		"""Will be called when user resumes a paused file."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onPlayBackSeek(self, time, seekOffset):
		"""
		onPlayBackSeek method.

		:param time: integer - time to seek to.
		:param seekOffset: integer - ?.

		Will be called when user seeks to a time
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onPlayBackSeekChapter(self, chapter):
		"""
		onPlayBackSeekChapter method.

		:param chapter: integer - chapter to seek to.

		Will be called when user performs a chapter seek
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onPlayBackSpeedChanged(self, speed):
		"""
		onPlayBackSpeedChanged(speed) -- onPlayBackSpeedChanged method.

		:param speed: integer - current speed of player.

		.. note:: negative speed means player is rewinding, 1 is normal playback speed.

		Will be called when players speed changes. (eg. user FF/RW)
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def onQueueNextItem(self):
		"""
		onQueueNextItem method.

		Will be called when player requests next item
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def isPlaying(self):
		"""Returns ``True`` is xbmc is playing a file."""
		return self.is_playing

	def isPlayingAudio(self):
		"""Returns ``True`` is xbmc is playing an audio file."""
		return self.isPlaying()

	def isPlayingVideo(self):
		"""Returns ``True`` if xbmc is playing a video."""
		return self.isPlaying()

	def getPlayingFile(self):
		"""
		returns the current playing file as a string.

		.. note:: For LiveTV, returns a pvr:// url which is not translatable to an OS specific file or external url

		:raises: Exception, if player is not playing a file.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getVideoInfoTag(self):
		"""Returns the VideoInfoTag of the current playing Movie.

		:raises: Exception: If player is not playing a file or current file is not a movie file.

		.. note:: This doesn't work yet, it's not tested.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return InfoTagVideo()

	def getMusicInfoTag(self):
		"""Returns the MusicInfoTag of the current playing 'Song'.

		:raises: Exception: If player is not playing a file or current file is not a music file.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return InfoTagMusic()

	def getTotalTime(self):
		"""Returns the total time of the current playing media in seconds.

		This is only accurate to the full second.

		:raises: Exception: If player is not playing a file.
		"""
		return self.total

	def getTime(self):
		"""Returns the current time of the current playing media as fractional seconds.

		:raises: Exception: If player is not playing a file.
		"""
		return self.time

	def seekTime(self, pTime):
		"""Seeks the specified amount of time as fractional seconds.

		The time specified is relative to the beginning of the currently playing media file.

		:raises: Exception: If player is not playing a file.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def setSubtitles(self, subtitleFile):
		"""Set subtitle file and enable subtitles.

		:param subtitleFile: string or unicode - Path to subtitle.

		Example::

			setSubtitles('/path/to/subtitle/test.srt')
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def getSubtitles(self):
		"""Get subtitle stream name."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def disableSubtitles(self):
		"""Disable subtitles."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def getAvailableAudioStreams(self):
		"""Get audio stream names."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return list()

	def getAvailableSubtitleStreams(self):
		"""
		get Subtitle stream names
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return list()

	def setAudioStream(self, iStream):
		"""Set audio stream.

		:param iStream: int
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def setSubtitleStream(self, iStream):
		"""
		set Subtitle Stream

		:param iStream: int

		example::

			setSubtitleStream(1)
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def showSubtitles(self, bVisible):
		"""
		enable/disable subtitles

		:param bVisible: boolean - ``True`` for visible subtitles.

		example::

			xbmc.Player().showSubtitles(True)
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

class PlayList(object):
	"""Retrieve a reference from a valid xbmc playlist

	:param playlist: int - can be one of the next values:

	::

		0: xbmc.PLAYLIST_MUSIC
		1: xbmc.PLAYLIST_VIDEO

	Use PlayList[int position] or __getitem__(int position) to get a PlayListItem.
	"""

	def __new__(cls, playList):
		if playList == PLAYLIST_MUSIC:
			try:
				global playlist_0
				return playlist_0
			except:
				ans = super(PlayList, cls).__new__(cls, playList)
				playlist_0 = ans
				return ans
		elif playList == PLAYLIST_VIDEO:
			try:
				global playlist_1
				return playlist_1
			except:
				ans = super(PlayList, cls).__new__(cls, playList)
				playlist_1 = ans
				return ans
		else:
			raise Exception('Cannot create playlist with type {}'.format(playList))
	def __init__(self, playList):
		"""Retrieve a reference from a valid xbmc playlist

		playlist: int - can be one of the next values:

		::

			0: xbmc.PLAYLIST_MUSIC
			1: xbmc.PLAYLIST_VIDEO

		Use PlayList[int position] or __getitem__(int position) to get a PlayListItem.
		"""
		self.playlist = []
		self.position = -1

	def __getitem__(self, item):
		"""x.__getitem__(y) <==> x[y]"""
		return self.playlist.__getitem__(item)

	def __len__(self):
		"""x.__len__() <==> len(x)"""
		return self.playlist.__len__()

	def add(self, url, listitem=None, index=-1):
		"""Adds a new file to the playlist.

		:param url: string or unicode - filename or url to add.
		:param listitem: listitem - used with setInfo() to set different infolabels.
		:param index: integer - position to add playlist item.

		Example::

			playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			video = 'F:\\movies\\Ironman.mov'
			listitem = xbmcgui.ListItem('Ironman', thumbnailImage='F:\\movies\\Ironman.tbn')
			listitem.setInfo('video', {'Title': 'Ironman', 'Genre': 'Science Fiction'})
			playlist.add(url=video, listitem=listitem, index=7)
		"""
		if index==-1:
			self.playlist.append({'url':url, 'listitem':listitem})
		else:
			self.playlist.insert(index, {'url':url, 'listitem':listitem})

	def load(self, filename):
		"""Load a playlist.

		Clear current playlist and copy items from the file to this Playlist.
		filename can be like .pls or .m3u ...

		:param filename:
		:return: ``False`` if unable to load playlist, True otherwise.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return False

	def remove(self, filename):
		"""Remove an item with this filename from the playlist.

		:param filename:
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def clear(self):
		"""Clear all items in the playlist."""
		self.playlist = []

	def shuffle(self):
		"""Shuffle the playlist."""
		random.shuffle(self.playlist)

	def unshuffle(self):
		"""Unshuffle the playlist."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def size(self):
		"""Returns the total number of PlayListItems in this playlist."""
		return len(self.playlist)

	def getposition(self):
		"""Returns the position of the current song in this playlist."""
		return self.position

	def getPlayListId(self):
		"""getPlayListId() --returns an integer."""
		return id(self)

playlist_0 = PlayList(PLAYLIST_MUSIC)
playlist_1 = PlayList(PLAYLIST_VIDEO)

class PlayListItem(object):
	"""Creates a new PlaylistItem which can be added to a PlayList."""

	def getdescription(self):
		"""Returns the description of this PlayListItem."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getduration(self):
		"""Returns the duration of this PlayListItem."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return long()

	def getfilename(self):
		"""Returns the filename of this PlayListItem."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()


class InfoTagMusic(object):
	"""InfoTagMusic class"""
	def getURL(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getTitle(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getArtist(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getAlbumArtist(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getAlbum(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getGenre(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getDuration(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getTrack(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getDisc(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getTrackAndDisc(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getReleaseDate(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getListeners(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getPlayCount(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getLastPlayed(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getComment(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getLyrics(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()


class InfoTagVideo(object):
	"""InfoTagVideo class"""
	def getDirector(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getWritingCredits(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getGenre(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getTagLine(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getPlotOutline(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getPlot(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getPictureURL(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getTitle(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getOriginalTitle(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getVotes(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getCast(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getFile(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getPath(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getIMDBNumber(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getYear(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getPremiered(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getFirstAired(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getRating(self):
		"""Returns a float."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return float()

	def getPlayCount(self):
		"""Returns an integer."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getLastPlayed(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getTVShowTitle(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getMediaType(self):
		"""Returns a string."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getSeason(self):
		"""Returns an int."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getEpisode(self):
		"""Returns an int."""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()


class Monitor(object):
	"""
	Monitor class.

	Creates a new Monitor to notify addon about changes.
	"""
	def __init__(self):
		import traceback
		stack = traceback.extract_stack()[:-1]
		print 'searching for id in {}'.format(stack)
		for s in stack:
			m = re.search(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', '([^{}]+)'.format(os.path.sep)).encode('string-escape'), s[0])
			if m:
				print 'Found id {}'.format(m.group(1))
				self.id = m.group(1)
				break
		if not self.id:
			raise Exception('Could not find addon ID automatically')
		self.abort = False
		bridge.register_for_trigger(kodi_utils.TRIGGER_SETTINGS_CHANGED, bridge.thread.id, kodi_utils.trigger_listener_for_settings(self.id, self.onSettingsChanged))
		bridge.register_for_trigger(kodi_utils.TRIGGER_ABORT, bridge.thread.id, kodi_utils.trigger_listener_for_abort(self.id, self.onAbortRequested))

	def onAbortRequested(self):
		"""
		.. warning:: Deprecated!
		"""
		self.abort = True

	def onDatabaseUpdated(self, database):
		"""
		.. warning:: Deprecated!
		"""
		pass

	def onScreensaverActivated(self):
		"""
		onScreensaverActivated method.

		Will be called when screensaver kicks in
		"""
		pass

	def onScreensaverDeactivated(self):
		"""
		onScreensaverDeactivated method.

		Will be called when screensaver goes off
		"""
		pass

	def onSettingsChanged(self):
		"""
		onSettingsChanged method.

		Will be called when addon settings are changed
		"""
		pass

	def onDatabaseScanStarted(self, database):
		"""
		.. warning:: Deprecated!
		"""
		pass

	def onNotification(self, sender, method, data):
		"""
		onNotification method.

		:param sender: str - sender of the notification
		:param method: str - name of the notification
		:param data: str - JSON-encoded data of the notification

		Will be called when Kodi receives or sends a notification
		"""
		pass

	def onCleanStarted(self, library):
		"""
		onCleanStarted method.

		:param library: video/music as string

		Will be called when library clean has started
		and return video or music to indicate which library is being cleaned
		"""
		pass

	def onCleanFinished(self, library):
		"""
		onCleanFinished method.

		:param library: video/music as string

		Will be called when library clean has ended
		and return video or music to indicate which library has been cleaned
		"""
		pass

	def onDPMSActivated(self):
		"""
		onDPMSActivated method.

		Will be called when energysaving/DPMS gets active
		"""
		pass

	def onDPMSDeactivated(self):
		"""
		onDPMSDeactivated method.

		Will be called when energysaving/DPMS is turned off
		"""
		pass

	def onScanFinished(self, library):
		"""
		onScanFinished method.

		:param library: video/music as string

		Will be called when library scan has ended
		and return video or music to indicate which library has been scanned
		"""
		pass

	def onScanStarted(self, library):
		"""
		onScanStarted method.

		:param library: video/music as string

		Will be called when library scan has started
		and return video or music to indicate which library is being scanned
		"""
		pass

	def waitForAbort(self, timeout=-1):
		"""
		Block until abort is requested, or until timeout occurs.

		If an abort requested have already been made, return immediately.
		Returns ``True`` when abort have been requested,
		``False`` if a timeout is given and the operation times out.

		:param timeout: float - (optional) timeout in seconds. Default: no timeout.
		:return: bool
		"""
		if timeout!=-1:
			now = time.time()
			while time.time() - now < timeout and not abortRequested:
				time.sleep(1)
		else:
			while not abortRequested:
				time.sleep(1)
		return abortRequested

	def abortRequested(self):
		"""
		Returns ``True`` if abort has been requested.
		"""
		return self.abort


class RenderCapture(object):
	"""RenerCapture class"""
	def capture(self, width, height, flags=0):
		"""
		Issue capture request.

		:param width: Width capture image should be rendered to
		:param height: Height capture image should should be rendered to
		:param flags: Optional. Flags that control the capture processing.

		The value for 'flags' could be or'ed from the following constants:

		- ``xbmc.CAPTURE_FLAG_CONTINUOUS``: after a capture is done,
		  issue a new capture request immediately
		- ``xbmc.CAPTURE_FLAG_IMMEDIATELY``: read out immediately whencapture() is called,
		  this can cause a busy wait

		.. warning:: As of Kodi 17.x (Krypton) ``flags`` option will be depreciated.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		pass

	def getAspectRatio(self):
		"""
		:return: aspect ratio of currently displayed video as a float number.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return float()

	def getCaptureState(self):
		"""
		:return: processing state of capture request.

		The returned value could be compared against the following constants::

		- ``xbmc.CAPTURE_STATE_WORKING``: Capture request in progress.
		- ``xbmc.CAPTURE_STATE_DONE``: Capture request done. The image could be retrieved withgetImage()
		- ``xbmc.CAPTURE_STATE_FAILED``: Capture request failed.

		.. warning:: Will be depreciated in Kodi 17.x (Krypton)
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getHeight(self):
		"""
		:return: height of captured image.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def getImage(self, msecs=0):
		"""
		Get image

		:param msecs: wait time in msec
		:return: captured image as a bytearray.

		.. note:: ``msec`` param will be added in Kodi 17.x (Krypton).

		The size of the image isgetWidth() * getHeight() * 4
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return bytearray()

	def getImageFormat(self):
		"""
		:return: format of captured image: 'BGRA' or 'RGBA'.

		.. note:: As of Kodi 17.x (Krypton) 'BRRA' will always be returned
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return str()

	def getWidth(self):
		"""
		:return: width of captured image.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()

	def waitForCaptureStateChangeEvent(self, msecs=0):
		"""
		wait for capture state change event

		:param msecs: Milliseconds to wait. Waits forever if not specified.

		The method will return ``1`` if the Event was triggered. Otherwise it will return ``0``.
		"""
		logger.warning('{}.{}.{} not implemented'.format(__name__, self.__class__.__name__, sys._getframe().f_code.co_name))
		return int()


def audioResume():
	"""
	Resume Audio engine.

	example::

		xbmc.audioResume()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def audioSuspend():
	"""
	Suspend Audio engine.

	example::

		xbmc.audioSuspend()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def convertLanguage(language, format):
	"""
	Returns the given language converted to the given format as a string.

	:param language: string either as name in English, two letter code (ISO 639-1),
		or three letter code (ISO 639-2/T(B)
	:param format: format of the returned language string:

	- ``xbmc.ISO_639_1``: two letter code as defined in ISO 639-1
	- ``xbmc.ISO_639_2``: three letter code as defined in ISO 639-2/T or ISO 639-2/B
	- ``xbmc.ENGLISH_NAME``: full language name in English (default)

	example::

		language = xbmc.convertLanguage(English, xbmc.ISO_639_2)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def enableNavSounds(yesNo):
	"""
	Enables/Disables nav sounds

	:param yesNo: enable (``True``) or disable (``False``) nav sounds

	example::

		xbmc.enableNavSounds(True)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def executeJSONRPC(jsonrpccommand):
	"""
	Execute an JSONRPC command.

	:param jsonrpccommand: string - jsonrpc command to execute.

	List of commands: http://wiki.xbmc.org/?title=JSON-RPC_API

	example::

		response = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "JSONRPC.Introspect", "id": 1 }')
	"""
	logger.warning('{}.{}({}) not implemented'.format(__name__, sys._getframe().f_code.co_name, jsonrpccommand))
	return str()


def executebuiltin(function, wait=False):
	"""
	Execute a built in XBMC function.

	:param function: string - builtin function to execute.

	List of functions: http://wiki.xbmc.org/?title=List_of_Built_In_Functions

	example::

		xbmc.executebuiltin('XBMC.RunXBE(c:\avalaunch.xbe)')
	"""
	logger.debug('evaluating {}'.format(function))

	m = re.search('.*Container.Update\(plugin://([^/]*)(.*)\)', function)
	if m:
		bridge.saveSettings()
		bridge._message({'type':'load', 'url':'/catalog/{}'.format(kodi_utils.b64encode(m.group(1))), 'data':kodi_utils.b64encode(m.group(2))})
		return str()
	m = re.search('.*Container.Update\((.*)\)', function)
	if m:
		bridge.saveSettings()
		bridge._message({'type':'load', 'url':'/catalog/{}'.format(kodi_utils.b64encode(Container.plugin.id)), 'data':kodi_utils.b64encode(m.group(1))})
		return str()
	m = re.search('.*Container.Refresh.*', function)
	if m:
		bridge.saveSettings()
		bridge._message({'type':'refresh'})
		return str()
	m = re.search('.*RunPlugin\(plugin://([^/]*)(.*)\)', function)
	if m:
		bridge.saveSettings()
		bridge._message({'type':'load', 'url':'/catalog/{}'.format(kodi_utils.b64encode(m.group(1))), 'data':kodi_utils.b64encode(m.group(2))})
		return str()
	m = re.search('.*RunPlugin\((.*)\)', function)
	if m:
		bridge.saveSettings()
		bridge._message({'type':'load', 'url':'/catalog/{}'.format(kodi_utils.b64encode(Container.plugin.id)), 'data':kodi_utils.b64encode(m.group(1))})
		return str()
	m = re.search('Notification\(([^,]*), ([^,]*)(, ([^,]*), ([^,]*))*\)', function)
	if m:
		title = m.group(1)
		message = m.group(2)
		timeout = m.group(4)
		icon = m.group(5)
		bridge.alertdialog(title, message, timeout)
		return str()
	m = re.search('.*Extract\(([^,]*), ([^,]*)\)', function)
	if m:
		zip = m.group(1)
		dir = m.group(2)
		if not zipfile.is_zipfile(zip):
			raise Exception('{} is not a valid zip file'.format(zip))
		if not os.path.exists(dir):
			os.pmakedirs(dir)
		if not os.path.isdir(dir):
			raise Exception('{} is not a dir or cannot be created'.format(dir))
		with zipfile.ZipFile(zip, 'r') as f:
				f.extractall(dir)
				return str()
	logger.warning('{}.{}({}) not implemented'.format(__name__, sys._getframe().f_code.co_name, function))
	return str()


def executescript(script):
	"""
	Execute a python script.

	:param script: string - script filename to execute.

	example::

		xbmc.executescript('special://home/scripts/update.py')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def getCacheThumbName(path):
	"""
	Returns a thumb cache filename.

	:param path: string or unicode -- path to file

	Example::

		thumb = xbmc.getCacheThumbName('f:\videos\movie.avi')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getCleanMovieTitle(path, usefoldername=False):
	"""
	Returns a clean movie title and year string if available.

	:param path: string or unicode - String to clean
	:param usefoldername: [opt] bool - use folder names (defaults to ``False``)

	example::

		title, year = xbmc.getCleanMovieTitle('/path/to/moviefolder/test.avi', True)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return tuple()


def getCondVisibility(condition):
	"""
	Returns ``True`` (``1``) or ``False`` (``0``) as a ``bool``.

	:param condition: string - condition to check.

	List of Conditions: http://wiki.xbmc.org/?title=List_of_Boolean_Conditions

	.. note:: You can combine two (or more) of the above settings by using "+" as an ``AND`` operator,
		"|" as an ``OR`` operator, "!" as a ``NOT`` operator, and "[" and "]" to bracket expressions.

	example::

		visible = xbmc.getCondVisibility('[Control.IsVisible(41) + !Control.IsVisible(12)]')
	"""
	#'Window.IsActive(virtualkeyboard)'
	if condition == 'Window.IsActive(virtualkeyboard)':
		return False
	if condition == 'Window.IsActive(yesnoDialog)':
		return False
	if condition == 'Window.IsVisible(progressdialog)':
		return False
	m = re.search('(!*)System.HasAddon\((.*)\)', condition)
	if m:
		neg = m.group(1) == '!'
		if neg:
			return not os.path.isdir(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', m.group(2)))
		else:
			return os.path.isdir(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'addons', m.group(2)))
	if condition == 'Library.IsScanningVideo':
		return False
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))	
	return bool(1)


def getDVDState():
	"""
	Returns the dvd state as an integer.

	return values are:

	- 1 : ``xbmc.DRIVE_NOT_READY``
	- 16 : ``xbmc.TRAY_OPEN``
	- 64 : ``xbmc.TRAY_CLOSED_NO_MEDIA``
	- 96 : ``xbmc.TRAY_CLOSED_MEDIA_PRESENT``

	example::

		dvdstate = xbmc.getDVDState()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return long()


def getFreeMem():
	"""
	Returns the amount of free memory in MB as an integer.

	example::

		freemem = xbmc.getFreeMem()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return long()


def getGlobalIdleTime():
	"""
	Returns the elapsed idle time in seconds as an integer.

	example::

		t = xbmc.getGlobalIdleTime()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return long()


def getIPAddress():
	"""
	Returns the current ip address as a string.

	example::

		ip = xbmc.getIPAddress()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getInfoImage(infotag):
	"""
	Returns a filename including path to the InfoImage's thumbnail as a string.

	:param infotag: string - infotag for value you want returned.

	List of InfoTags: http://wiki.xbmc.org/?title=InfoLabels

	example::

		filename = xbmc.getInfoImage('Weather.Conditions')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getInfoLabel(cLine):
	"""
	Returns an InfoLabel as a string.

	:param cLine: string - infoTag for value you want returned.

	List of InfoTags: http://wiki.xbmc.org/?title=InfoLabels

	example::

		label = xbmc.getInfoLabel('Weather.Conditions')
	"""
	if cLine == 'Container.PluginName':
		return Container.plugin.id
	if cLine == 'System.BuildVersion':
		return '17.0'
	logger.warning('{}.{}({}) not implemented'.format(__name__, sys._getframe().f_code.co_name, cLine))
	return str()


def getLanguage(format=ENGLISH_NAME, region=False):
	"""
	Returns the active language as a string.

	:param format: [opt] format of the returned language string

	- ``xbmc.ISO_639_1``: two letter code as defined in ISO 639-1
	- ``xbmc.ISO_639_2``: three letter code as defined in ISO 639-2/T or ISO 639-2/B
	- ``xbmc.ENGLISH_NAME``: full language name in English (default)

	:param region: [opt] append the region delimited by "-" of the language (setting)
		to the returned language string

	example::

		language = xbmc.getLanguage(xbmc.ENGLISH_NAME)
	"""
	if format == ENGLISH_NAME:
		return LANGUAGE
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getLocalizedString(id):
	"""
	Returns a localized 'unicode string'.

	:param id: integer -- id# for string you want to localize.

	.. note:: See strings.po in language folders for which id you need for a string.

	example::

		locstr = xbmc.getLocalizedString(6)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return unicode()


def getRegion(id):
	"""
	Returns your regions setting as a string for the specified id.

	:param id: string - id of setting to return

	.. note:: choices are (dateshort, datelong, time, meridiem, tempunit, speedunit)
		You can use the above as keywords for arguments.

	example::

		date_long_format = xbmc.getRegion('datelong')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getSkinDir():
	"""
	Returns the active skin directory as a string.

	.. note:: This is not the full path like ``'special://home/addons/skin.confluence'``,
		but only ``'skin.confluence'``.

	example::

		skindir = xbmc.getSkinDir()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def getSupportedMedia(mediaType):
	"""
	Returns the supported file types for the specific media as a string.

	:param mediaType: string - media type

	.. note:: media type can be (video, music, picture).
		The return value is a pipe separated string of filetypes (eg. '.mov|.avi').

	You can use the above as keywords for arguments.

	example::

		mTypes = xbmc.getSupportedMedia('video')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def log(msg, level=LOGNOTICE):
	"""
	Write a string to XBMC's log file and the debug window.

	:param msg: string - text to output.
	:param level: [opt] integer - log level to ouput at. (default=``LOGNOTICE``)

	.. note:: You can use the above as keywords for arguments and skip certain optional arguments.
		Once you use a keyword, all following arguments require the keyword.

	.. warning:: Starting from Kodi 16.0 (Jarvis) default level will be changed to ``LOGDEBUG``.

	Text is written to the log for the following conditions.

	- XBMC loglevel == -1 (NONE, nothing at all is logged)
	- XBMC loglevel == 0 (NORMAL, shows LOGNOTICE, LOGERROR, LOGSEVERE and LOGFATAL) * XBMC loglevel == 1
		(DEBUG, shows all)

	See pydocs for valid values for level.

	example::

		xbmc.log('This is a test string.', level=xbmc.LOGDEBUG)
	"""
	conv = {
	LOGDEBUG: logging.DEBUG, 
	LOGERROR: logging.ERROR,
	LOGFATAL: logging.FATAL,
	LOGINFO: logging.INFO,
	LOGNONE: logging.DEBUG,
	LOGNOTICE: logging.INFO,
	LOGSEVERE: logging.ERROR,
	LOGWARNING: logging.WARNING
	}
	logger.log(conv[level], msg)


def makeLegalFilename(filename, fatX=True):
	"""
	Returns a legal filename or path as a string.

	:param filename: string or unicode -- filename/path to make legal
	:param fatX: [opt] bool -- ``True`` = Xbox file system(Default)


	.. note: If fatX is ``True`` you should pass a full path.
		If fatX is ``False`` only pass the basename of the path.

	You can use the above as keywords for arguments and skip certain optional arguments.
	Once you use a keyword, all following arguments require the keyword.

	Example::

		filename = xbmc.makeLegalFilename('F: Age: The Meltdown.avi')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return str()


def playSFX(filename, useCached=True):
	"""
	Plays a wav file by filename

	:param filename: string - filename of the wav file to play.
	:param useCached: [opt] bool - False = Dump any previously cached wav associated with filename

	example::

		xbmc.playSFX('special://xbmc/scripts/dingdong.wav')
		xbmc.playSFX('special://xbmc/scripts/dingdong.wav',False)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def stopSFX():
	"""
	Stops wav file

	example::

		xbmc.stopSFX()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def restart():
	"""
	Restart the htpc.

	example::

		xbmc.restart()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass

def shutdown():
	"""
	Shutdown the htpc.

	example::

		xbmc.shutdown()
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def skinHasImage(image):
	"""
	Returns ``True`` if the image file exists in the skin.

	:param image: string - image filename

	.. note:: If the media resides in a subfolder include it.
		(eg. home-myfiles\home-myfiles2.png). You can use the above as keywords for arguments.

	example::

		exists = xbmc.skinHasImage('ButtonFocusedTexture.png')
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return bool(1)


def sleep(timemillis):
	"""
	Sleeps for 'time' msec.

	:param timemillis: integer - number of msec to sleep.

	.. note: This is useful if you have for example aPlayer class that is waiting
		for onPlayBackEnded() calls.

	:raises: TypeError, if time is not an integer.

	Example::

		xbmc.sleep(2000) # sleeps for 2 seconds
	"""
	time.sleep(timemillis/1000)


def startServer(iTyp, bStart, bWait=False):
	"""
	start or stop a server.

	:param iTyp: integer -- use SERVER_* constants
	:param bStart: bool -- start (True) or stop (False) a server
	:param bWait : [opt] bool -- wait on stop before returning (not supported by all servers)
	:return: bool -- ``True`` or ``False``


	Example::

		xbmc.startServer(xbmc.SERVER_AIRPLAYSERVER, False)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	pass


def translatePath(path):
	"""
	Returns the translated path.

	:param path: string or unicode - Path to format

	.. note: Only useful if you are coding for both Linux and Windows.

	Converts ``'special://masterprofile/script_data'`` -> ``'/home/user/XBMC/UserData/script_data'`` on Linux.

	Example::

		fpath = xbmc.translatePath('special://masterprofile/script_data')
		xbmc.translatePath(/Users/guyerlich/.TVMLSERVER/addons/plugin.video.nbcsnliveextra)
	"""
	if "special://home" in path :
		return path.replace("special://home", os.path.join(os.path.expanduser("~"), '.TVMLSERVER')).replace('/', os.path.sep)
	if 'special://profile/addon_data' in path:
		ans = path.replace('special://profile/addon_data', '{}'.format(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'userdata'))).replace('/', os.path.sep)
		if not os.path.isdir(ans):
			os.makedirs(ans)
		return ans
	if 'special://temp' in path:
		return path.replace('special://temp', '{}'.format(tempfile.gettempdir())).replace('/', os.path.sep)
	if 'special://xbmc' in path:
		return path.replace('special://xbmc', os.path.dirname(sys.executable)).replace('/', os.path.sep)
	if 'special://masterprofile' in path:
		ans = path.replace('special://masterprofile', '{}'.format(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'userdata'))).replace('/', os.path.sep)
		if not os.path.isdir(ans):
			os.makedirs(ans)
		return ans
	if 'special://userdata' in path:
		ans = path.replace('special://userdata', '{}'.format(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'userdata'))).replace('/', os.path.sep)
		if not os.path.isdir(ans):
			os.makedirs(ans)
		return ans
	if 'special://database' in path:
		ans = path.replace('special://database', '{}'.format(os.path.join(os.path.expanduser("~"), '.TVMLSERVER', 'userdata', Container.plugin.id))).replace('/', os.path.sep)
		if not os.path.isdir(ans):
			os.makedirs(ans)
		return ans

	logger.warning('{}.{}({}) not implemented'.format(__name__, sys._getframe().f_code.co_name, path))
	return path


def validatePath(path):
	"""
	Returns the validated path.

	:param path: string or unicode - Path to format

	.. note:: Only useful if you are coding for both Linux and Windows for fixing slash problems.
		e.g. Corrects 'Z://something' -> 'Z:'

	Example::

		fpath = xbmc.validatePath(somepath)
	"""
	logger.warning('{}.{} not implemented'.format(__name__, sys._getframe().f_code.co_name))
	return unicode()
