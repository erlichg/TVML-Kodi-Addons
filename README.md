# TVMLServer
Working TVML server written in python(flask) and javascript

##Prerequistes
- Python 2.7
- Flask http://flask.pocoo.org
- Gevent
- That's it!!

##How to use
Simply run the app.py located in repository root directory and start accepting TVML connection from your apple TV using a TVML client like: TVMLExplorer

##Plugins
You can write plugins (in the plugins directory) which will serve content back to the apple tv.
Just add a plugin dir with addon.xml, icon and main script.
The script must have a main function which will be called with 2 parameters: bridge and url
The script must return a list (may be empty) of Item objects
The app in turn will translate the list of items into an XML template to be sent to the client TVML app

#bridge
The bridge is your utilities class for various interactions with the client.
Method include:
```
- inputdialog(title, description) - pops an input dialog with text field to the user. Returns the response
- progressdialog(heading, line1, line2, line3) - shows a progress dialog. returns immediately
- updateprogressdialog(percent, heading, line1, line2, line3) - update the active progress dialog with these values. Returns immediately
- isprogresscanceled() - returns true/false whether progress dialog is showing or user aborted it
- closeprogress() - close the active progress dialog
- selectdialog(title, list) - shows a dialog with list of items. Waits until user has made a selection
- play(url) - invoke the player on a stream url. Returns immediately
- isplaying() - returns true/false whether player is still active
```

#url
The main function is initially called with an empty string.
if script was previously called and returned a list of Item objects, each item has a url attribute.
Once the user selects an Item, the script will be called again with the selected Item url attribute to get a new list of Item objects

#Item
Item object definition:
```
def __init__(self, url, title, subtitle=None, icon=None, details=None, info={})
```

##Example
Please check demo plugin in the plugins folder

##What's next
A lot more work to be done.
- implement more elaborate bridge functions
- implement a better mechanism for communication between server and javascript (i.e. client). Currently it relies on constant polling by client
