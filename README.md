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
![alt tag](https://raw.githubusercontent.com/ggyeh/TVML-Kodi-Addons/master/images/screenshot2.png)
![alt tag](https://raw.githubusercontent.com/ggyeh/TVML-Kodi-Addons/master/images/screenshot3.png)
![alt tag](https://raw.githubusercontent.com/ggyeh/TVML-Kodi-Addons/master/images/screenshot4.png)

##How to use
1. Simply run the app.py located in repository root directory.
2. This will run the server on port 5000.
3. Fire up a TVML client on the apple TV like: TVML Explorer (available in TVOS appstore)
4. Add your IP of the server
5. Have fun

##Kodi plugins
What I've got working so far are:
- Exodus
- KIDSIL
- Reshet
- Channel10
- and more

Most (simple) addons should work immediately (Simply place the unzipped kodi addon under the kodiplugins folder).

###XML templates
The main page of the app is the main.xml template which shows a grid view of all plugins available.

Once you select a plugin, the plugin will be called with an empty string and all consequent templates will be rendered based on plugin returns.

The app will transform the list of items to a template with this logic:
- If items have title, subtitle, icon and details, it will render the richest template available (list.xml) which shows all these details
- If items have only title and icon, it will render the grid.xml template (i.e. just a grid of images without details)
- if items have only title, it will render the barest template possible (nakedlist.xml) which is basically just a list of items


##Example
Please check available plugins in the kodiplugins folder

##What's working and what's not
The server is based on python flask and is relatively small scale.

The idea is to install the server (on your network) and access it locally (i.e. one user)

To create a large scale server serving multiple clients will probably require some work

Currently working are most dialogs, simple actions like addDirectory and setResolvedURL

executeBuiltin commands include Container.Update

Addon settings can be accessed by long press on the addon icon in the main view

Addon settings are saved locally (on client) so will persist even if server restarts

Addon data path (for saving local files) is currently on server so all clients will use the same files (might be a problem).

##What's next
A lot more work to be done:
- Implement more of kodi stubs to fit more addons
- Make use of VLC as a player to support streams that Apple built-in player does not. This will require AppStore app support off course 
- Modify the server to be able to accept many multiple connections. Think about the possibility to have multiple central servers on the web so everyone can connect to them without having to install anything locally!!
- If your interested in coding (python/javascript), I'd love the help

## License

Licensed under Apache License v2.0.
<br>
Copyright 2016
