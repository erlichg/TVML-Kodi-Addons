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

###XML templates
The main page of the app is the main.xml template which shows a grid view of all plugins available.

One you select a plugin, the plugin will be called with an empty string and all consequent templates will be rendered based on plugin returns.

The app will transform the list of items to a template with this logic:
- If items have title, subtitle, icon and details, it will render the richest template available (list.xml) which shows all these details
- If items have only title and icon, it will render the grid.xml template (i.e. just a grid of images without details)
- if items have only title, it will render the barest template possible (nakedlist.xml) which is basically just a list of items

###bridge
The bridge is your utilities class for various interactions with the client.

Method include:
```
- alertdialog(title, description) - pops an alert dialog to the user
- inputdialog(title, description, placeholder, button) - pops an input dialog with text field to the user. placeholder is the placeholder of the textfield. button is the button text. Returns the response
- progressdialog(heading, text) - shows a progress dialog. returns immediately
- updateprogressdialog(value, text) - update the active progress dialog with these values. Returns immediately
- isprogresscanceled() - returns true/false whether progress dialog is showing or user aborted it
- closeprogress() - close the active progress dialog
- selectdialog(title, list) - shows a dialog with list of items. Waits until user has made a selection
- play(url, type) - invoke the player on a stream url. type can be either video ir audio. Returns immediately
- isplaying() - returns true/false whether player is still active
```

###url
The main function is initially called with an empty string.

if script was previously called and returned a list of Item objects, each item has a url attribute.

Once the user selects an Item, the script will be called again with the selected Item url attribute to get a new list of Item objects

###Item
Item object definition:
```
def __init__(self, url, title, subtitle=None, icon=None, details=None, info={})
```

##Example
Please check demo plugin in the plugins folder

##What's next
A lot more work to be done.
- implement more elaborate bridge functions

## License

Licensed under Apache License v2.0.
<br>
Copyright 2016 Guy Erlich
