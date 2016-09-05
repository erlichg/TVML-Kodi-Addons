# TVML Kodi Addons
Working TVML server written in python(flask) and javascript serving original KODI addons!!
I've created a bridge from the kodi plugins to the server using the excellent [Kodi stubs](https://github.com/romanvm/Kodistubs)

##Prerequistes
- Python 2.7
- Flask http://flask.pocoo.org
- Gevent
- That's it!!

##Screenshots
![alt tag](https://raw.githubusercontent.com/ggyeh/TVML-Kodi-Addons/master/images/screenshot1.png)

##How to use
Simply run the app.py located in repository root directory and start accepting TVML connection from your apple TV using a TVML client like: TVML Explorer (available in TVOS appstore)

##Plugins
You can write plugins (in the plugins directory) which will serve content back to the apple tv.

Just add a plugin dir with addon.xml, icon and main script.

The script must have a main function which will be called with 2 parameters: bridge and url

The script must return a list (may be empty) of Item objects

The app in turn will translate the list of items into an XML template to be sent to the client TVML app

##Kodi plugins
Simpley place the unzipped kodi addon under the kodiplugins folder

###XML templates
The main page of the app is the main.xml template which shows a grid view of all plugins available.

One you select a plugin, the plugin will be called with an empty string and all consequent templates will be rendered based on plugin returns.

The app will transform the list of items to a template with this logic:
- If items have title, subtitle, icon and details, it will render the richest template available (list.xml) which shows all these details
- If items have only title and icon, it will render the grid.xml template (i.e. just a grid of images without details)
- if items have only title, it will render the barest template possible (nakedlist.xml) which is basically just a list of items


##Example
Please check available plugin in the kodiplugins folder

##What's working and what's not
Currently working are simple addon actions like setResolvedURL, ListItem and addDirectoryItem

Also working are various dialogs like input, select, yesno, progress etc.

Working executeBuiltin commands include Container.Update

Addon settings can be accessed by long press on the addon icon in the main view

Currently addon files (settings, cache, etc) are saved locally on server which means that all clients get the same settings.

##What's next
A lot more work to be done.
- implement more elaborate bridge functions

## License

Licensed under Apache License v2.0.
<br>
Copyright 2016
