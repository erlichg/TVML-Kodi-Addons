/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

// Registry of attribute name used to define the URL to template (e.g. documentURL or menuBarDocumentURL)
// to controller type (e.g. DocumentController or MenuBarController)
const attributeToController = {};
const attributeKeys = [];

function registerAttributeName(type, func) {
    attributeToController[type] = func;
    attributeKeys.push(type);
}

function resolveControllerFromElement(elem) {
    for (var i = 0, key; i < attributeKeys.length; i++) {
        key = attributeKeys[i];
        if (elem.hasAttribute(key)) {
            return {
                type: attributeToController[key],
                url: elem.getAttribute(key)
            };
        }
    }
}

function DocumentController(documentLoader, documentURL, initial, data, replace, special, callback) {
    this.handleEvent = this.handleEvent.bind(this);
    this.handleHoldSelect = this.handleHoldSelect.bind(this);
    this._documentLoader = documentLoader;
    if (typeof initial == "boolean" && initial) {
	    //console.log("Clearing all documents");
		//navigationDocument.clear();
		var favs = loadFavourites();
		var language = loadLanguage();
		var proxy = loadProxy();
		documentLoader.fetchPost({
	    	initial: initial,	    	
        	url: documentURL,
        	data: btoa(JSON.stringify({'favs':JSON.stringify(favs), 'lang':language, 'proxy':proxy})),
        	success: function(document, isModal) {
        	    // Add the event listener for document
        	    // this.setupDocument(document);
				if (navigationDocument.documents.length !=0) {
                    const main = navigationDocument.documents[0];
                    navigationDocument.replaceDocument(document, main);
                } else {
					navigationDocument.pushDocument(document);
				}
        	    if (typeof callback != "undefined") {
        	    	callback('success');
				}
        	}.bind(this),
        	error: function(xhr) {
        	    const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
        	    this.handleDocument(alertDocument);
        	    if (typeof callback != "undefined") {
        	    	callback('error');
				}
        	}.bind(this),
        	abort: function() {
	    	    if (typeof callback != "undefined") {
        	    	callback('abort');
				}
        	}
    	}); 	       					
    } else if (typeof data != "undefined" && data != null) {
	    documentLoader.fetchPost({
	    	initial: initial,	    	
        	url: documentURL,
        	data: data,
        	success: function(document, isModal) {
        	    // Add the event listener for document
        	    //this.setupDocument(document);
        	    // Allow subclass to do custom handling for this document
        	    this.handleDocument(document, isModal, replace);
        	    if (typeof callback != "undefined") {
        	    	callback('success');
				}
        	}.bind(this),
        	error: function(xhr) {
        	    const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
        	    this.handleDocument(alertDocument);
        	    if (typeof callback != "undefined") {
        	    	callback('error');
				}
        	}.bind(this),
        	abort: function() {
	    	    if (typeof callback != "undefined") {
        	    	callback('abort');
				}
        	},
        	special: special
    	});
    } else {
    	documentLoader.fetchPost({
		    initial: false,
    	    url: documentURL,
    	    success: function(document, isModal) {
    	        // Add the event listener for document
    	        ///this.setupDocument(document);
    	        // Allow subclass to do custom handling for this document
    	        this.handleDocument(document, isModal, replace);
    	        if (typeof callback != "undefined") {
        	    	callback('success');
				}
    	    }.bind(this),
    	    error: function(xhr) {
    	        const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
    	        this.handleDocument(alertDocument);
    	        if (typeof callback != "undefined") {
        	    	callback('error');
				}
    	    }.bind(this),
    	    abort: function() {
		        if (typeof callback != "undefined") {
        	    	callback('abort');
				}
    	    },
    	    special: special
    	});
    }
}

registerAttributeName('documentURL', DocumentController);

DocumentController.prototype.setupDocument = function(document) {
    document.addEventListener("select", this.handleEvent);
    document.addEventListener("play", this.handleEvent);
    document.addEventListener("holdselect", this.handleHoldSelect);    
};

DocumentController.prototype.handleDocument = function(document, isModal, replace) {
    if (typeof isModal == "undefined") {
		if (typeof replace == "boolean" && replace && navigationDocument.documents.length > 1) {
			navigationDocument.removeDocument(navigationDocument.documents[navigationDocument.documents.length-1]); //remove previous document
		}
		console.log("pushing document");
		replaceLoadingDocument(document);
	} else {
		console.log("presenting modal document");
		removeLoadingDocument();
		navigationDocument.presentModal(document);
		document.addEventListener("select", function(e) {
			navigationDocument.dismissModal();
		});
	}
};

DocumentController.prototype.handleEvent = function(event) {
    const target = event.target;

    const controllerOptions = resolveControllerFromElement(target);
    if (controllerOptions) {
        const controllerClass = controllerOptions.type;
        const documentURL = controllerOptions.url;
        // Create the subsequent controller based on the atribute and its value. Controller would handle its presentation.
        new controllerClass(this._documentLoader, documentURL);
    }
    else if (target.tagName === 'description') {
        // Handle description tag, if no URL was specified
        const body = target.textContent;
        const alertDocument = createDescriptiveAlertDocument('', body);
        navigationDocument.presentModal(alertDocument);
    }
};

DocumentController.prototype.handleHoldSelect = function(event) {
	const target = event.target;
	if (target.getAttribute("onholdselect") != "") {
		eval(target.getAttribute("onholdselect"));
/*
		const documentURL = target.getAttribute("menuURL");
		if (documentURL != "") {
			var loadingDocument;
        	if (!DocumentController.preventLoadingDocument) {
        	    loadingDocument = createLoadingDocument();
        	    navigationDocument.pushDocument(loadingDocument);
        	}
        	// Create the subsequent controller based on the atribute and its value. Controller would handle its presentation.
			new DocumentController(this._documentLoader, documentURL, loadingDocument);
        }
*/
	}
}

const singleton_loading_document = createLoadingDocument();
function addLoadingDocument(title) {
	title = title || "Loading...";
	if (singleton_loading_document.getElementById("title").textContent != title) {
        singleton_loading_document.getElementById("title").textContent = title;
    }
	if (navigationDocument.documents.indexOf(singleton_loading_document)==navigationDocument.documents.length-1) {
		return;
	}
	if (navigationDocument.documents.indexOf(singleton_loading_document)!=-1) { //if loading document already on stack we need to remove it
        removeLoadingDocument();
    }
	navigationDocument.pushDocument(singleton_loading_document);

}

function removeLoadingDocument() {
	try {
		navigationDocument.removeDocument(singleton_loading_document);
	} catch (e) {
		//nothing to do
	}
}

function replaceLoadingDocument(newdoc) {
	if (navigationDocument.documents.indexOf(singleton_loading_document)!=-1) { //if loading document already on stack
    	navigationDocument.replaceDocument(newdoc, singleton_loading_document);
	} else {
		navigationDocument.pushDocument(newdoc);
	}
}

function clearPlay() {
	localStorage.setItem('playCache', '{}');
	localStorage.setItem('history', '{}');
	refreshMainScreen();
}

function clearSettings() {
	for (var i=0;i<localStorage.length;i++) {
		var key = localStorage.key(i);
		if (key!='playCache' && key!='history'&&key!='language'&&key!='favourites'&&key!='proxy') {
			localStorage.setItem(key, '{}');
		}
	}
	refreshMainScreen();
}

function clearAll() {
	localStorage.clear();
	refreshMainScreen();
}

function catalog(id, url) {
    if (typeof url == "undefined") {
        url = '';
    }
    favs = loadFavourites();
    language = loadLanguage();
    settings = loadSettings();
    history = loadHistory();
    post('/catalog/'+id, btoa(JSON.stringify({'favs':JSON.stringify(favs), 'lang':language, 'settings':settings, 'url':url, 'history':JSON.stringify(history)})))
}

function menu(id, url) {
    if (typeof url == "undefined") {
        url = '';
    }
    favs = loadFavourites();
    language = loadLanguage();
    settings = loadSettings();
    post('/menu/'+id, btoa(JSON.stringify({'favs':JSON.stringify(favs), 'lang':language, 'settings':settings, 'url':url})))
}

function notify(url, data) {
	console.log("notify: "+url);
	documentLoader.fetchPost({
		url:url,
		silent: true,
		data: data,
		abort: function() {
						
		},
		success: function() {
			
		},
		error: function() {
			
		}
	});
}

function load(url, initial, replace, callback) {
	console.log("loading "+url);
	new DocumentController(documentLoader, url, initial, null, replace, null, callback);
}

function post(url, data, callback) {
	console.log("posting "+url);
	new DocumentController(documentLoader, url, false, data, false, null, callback);
	
}

function saveSettings(settings) {
	//console.log("saving settings: "+JSON.stringify(settings));
	localStorage.setItem("addon_settings", JSON.stringify(settings));
}

function loadHistory() {
    var history = localStorage.getItem('history');
    if (history == null) {
        history = '{}';
    }
    try {
        history = JSON.parse(history);
    } catch (e) {
        console.log('Failed to parse history. '+e);
        history = {};
    }
    return history;
}

function loadSettings() {
	var addonSettings = localStorage.getItem("addon_settings");
    if(addonSettings == null) {
	    addonSettings = "{}";
    }
    try {
	    addonSettings = JSON.parse(addonSettings);
    } catch (e) {
	    addonSettings = {};
    }
    //console.log('Loaded addon settings '+JSON.stringify(addonSettings));
    return addonSettings;
}

function loadFavourites() {
	var favs = localStorage.getItem("favourites");
	if (favs == null) {
	    favs = "[]";
    }
	try {
		favs = JSON.parse(favs);
	} catch (e) {
		console.log("Error getting addonsSettings from local storage");
		favs = [];
	} 
    
    console.log('Loaded favourites '+JSON.stringify(favs));
    return favs;
}

function refreshMainScreen() {
    new DocumentController(documentLoader, startDocURL, true);
}

function toggleFavorites(addon) {
	var favs = loadFavourites();
	var index = favs.indexOf(addon);
	if (index > -1) {
    	favs.splice(index, 1);
	} else {
	    favs.push(addon);
	}
	localStorage.setItem('favourites', JSON.stringify(favs));
	refreshMainScreen();
}


function removeAddon(addon) {
	post('/removeAddon', btoa(addon), function() {
		refreshMainScreen();
	});
}

function installAddon(addon) {
    post('/installAddon', btoa(addon), function() {
    	refreshMainScreen();
	});
}

function loadProxy() {
	var proxy = localStorage.getItem("proxy");
	if (proxy == null) {
		proxy = "false";
	}
	return proxy;
}
function toggleProxy() {
	var proxy = loadProxy();
	if (proxy == "true") {
		proxy = "false";
	} else {
		proxy = "true";
	}
	notify("/toggleProxy");
	localStorage.setItem("proxy", proxy);
}

function restartServer() {
	documentLoader.fetchPost({
		url:'/restart',
		success: function() {
			
		},
		abort: function() {
			
		},
		error: function() {
			
		}
	});
	setTimeout(function() {
		new DocumentController(documentLoader, startDocURL, true);
	}, 5000);
}

function loadLanguage() {
	var lang = localStorage.getItem("language");
	if (lang == null) {
	    lang = "English";
    }
	console.log('Loaded language '+lang);
    return lang;
}

function selectLanguage() {
	const lang = loadLanguage()
	const available_languages = ["Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Azerbaijani", "Basque", "Belarusian", "Bosnian", "Bulgarian", "Burmese", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Esperanto", "Estonian", "Faroese", "Finnish", "French", "Galician", "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Korean", "Latvian", "Lithuanian", "Macedonian", "Malay", "Malayalam", "Maltese", "Maori", "Mongolian", "Norwegian", "Ossetic", "Persian", "Persian", "Polish", "Portuguese", "Romanian", "Russian", "Serbian", "Silesian", "Sinhala", "Slovak", "Slovenian", "Spanish", "Spanish", "Swedish", "Tajik", "Tamil", "Telugu", "Thai", "Turkish", "Ukrainian", "Uzbek", "Vietnamese", "Welsh"];
	showSelectDialog('Available Languages', available_languages, available_languages.indexOf(lang), function(ans) {
		if (typeof ans != "undefined") {
			localStorage.setItem("language", ans);			
		}
	});
}

var last_special = null;
var last_filter = null;
function browse(dir, filter, special) {
	if (typeof special == 'undefined' || special == null) {
		special = last_special;
	}
	if (typeof filter == 'undefined' || filter == null) {
	    filter = last_filter;
	}
	if (typeof special == 'undefined' || special == null) {
		console.log('when browsing must pass special function');
		return;
	}
	last_special = special;
	last_filter = filter;
	if (typeof dir == "undefined" || dir == null) {
		new DocumentController(documentLoader, '/browse', false, btoa(JSON.stringify({'dir':'', 'filter':filter})), true, special);
	} else {
		new DocumentController(documentLoader, '/browse', false, btoa(JSON.stringify({'dir':dir, 'filter':filter})), true, special);
	}
}

function showInputDialog(title, description, placeholder, button, secure, callback) {
	if(typeof description == "undefined") {
		description = '';
	}
	if(typeof placeholder == "undefined") {
		placeholder = '';
	}
	if(typeof button == "undefined") {
		button = 'OK';
	}
	if(typeof secure == "undefined") {
		secure = false;
	}
	var template = `<?xml version="1.0" encoding="UTF-8" ?>
	<document>
		<formTemplate>
			<banner>
				<title>${title}</title>
				<description>${description}</description> 
			</banner>               
			<textField id="text" secure="${secure}">${placeholder}</textField>		
			<footer>
				<button id="button">
					<text>${button}</text>
				</button>
			</footer>		 
		</formTemplate>
	</document>
	`;
	var dialog = new DOMParser().parseFromString(template, "application/xml");
	var sent_answer = false;
	dialog.getElementById("button").addEventListener("select", function() {
		var ans = dialog.getElementById("text").getFeature('Keyboard').text;
		callback(ans);
		sent_answer = true;
		navigationDocument.dismissModal(dialog);
	});
	dialog.addEventListener("unload", function() {
		if(!sent_answer) {
			callback();
		}
	});
	navigationDocument.presentModal(dialog);
}

function decode_utf8(s) {
    try {
        return decodeURIComponent(escape(s));
    } catch(e) {
        try {
            return decodeURIComponent(s);
        } catch(ee) {
            return s;
        }
    }
}

function showSelectDialog(title, choices, index, callback) {
	var template=`<?xml version="1.0" encoding="UTF-8" ?>
  <document>
	<head>
	  <style>
	  @media tv-template and (tv-theme:light) {
      	.foo { color:rgb(0, 0, 0); tv-tint-color:rgb(0,0,0); tv-highlight-color:rgb(0, 0, 0); tv-text-max-lines:15; tv-text-highlight-style: marquee-on-highlight; tv-minimum-scale-factor: 0.7; }
      	.foo2 { color:rgb(0, 0, 0); tv-highlight-color:rgb(0, 0, 0); tv-text-max-lines:15; }
		  .foo3 { tv-position:footer; tv-align:right; margin: 0; tv-tint-color:rgb(0,0,0); tv-highlight-color:rgb(0, 0, 0); }
	  }
	  @media tv-template and (tv-theme:dark) {
      	.foo { color:rgb(255, 255, 255); tv-tint-color:rgb(255,255,255); tv-highlight-color:rgb(0,0,0); tv-text-max-lines:15; tv-text-highlight-style: marquee-on-highlight; tv-minimum-scale-factor: 0.7; }
      	.foo2 { color:rgb(255, 255, 255); tv-highlight-color:rgb(255, 255, 255); tv-text-max-lines:15; }
		  .foo3 { tv-position:footer; tv-align:right; margin: 0; tv-tint-color:rgb(255,255,255); tv-highlight-color:rgb(255,255,255); }
	  }
	</style>
	  <banner>
         <title>${decode_utf8(title)}</title>
      </banner>
	</head>
	<listTemplate autoHighlight="true">
	  <list>
		  <section>`;
	for (var item in choices) {
		if (item == index) {
			template = template + `<listItemLockup autoHighlight="true">										
				 	<title class="foo">${decode_utf8(choices[item])}</title>
				</listItemLockup>`;
		} else {
			template = template + `<listItemLockup>										
				 	<title class="foo">${decode_utf8(choices[item])}</title>
				</listItemLockup>`;
		}
	}
	template = template +`</section>
	  </list>
	</listTemplate>
  </document>`;
  	var dialog = new DOMParser().parseFromString(template, "application/xml");
	var sent_answer = false;
	dialog.addEventListener("select", function(event) {
		sent_answer = true;
		navigationDocument.dismissModal(dialog);
		var ans = event.target.childNodes.item(0).textContent;
		callback(ans);				
	});
	dialog.addEventListener("unload", function() {
		if(!sent_answer) {
			callback();
		}
	});
	navigationDocument.presentModal(dialog);
}

function showInfoDialog(info) {
	var template=`
		<document>
    <productTemplate>
        <background>
        </background>
        <banner>
        	<infoList>
            <info>
               <header>
                  <title>Director</title>
               </header>
               <text>${info.director}</text>
            </info>
            <info>
               <header>
                  <title>Actors</title>
               </header>
               `;
               for (var i in info.cast) {
			   	template += `<text>${info.cast[i][0]}</text>`;
        		}
               template += `
            </info>
         </infoList>
            <stack>
                <title style="tv-text-max-lines: 3;">${info.title}</title>
                <row>
					<text><badge src="resource://tomato-fresh"/>${info.rating * 100 / 10}%</text>
					<text>${info.duration}</text>
					<text>${info.genre}</text>
					<text>${info.year}</text>
					<badge src="resource://mpaa-${info.mpaa}" class="badge" />
			   </row>
                <description style="tv-text-max-lines: 30;">${info.plot}</description>
            </stack>
            <heroImg src="${documentLoader.baseURL + info.poster}" />
        </banner>
    </productTemplate>
</document>
	`;
	var d = new DOMParser().parseFromString(template, "application/xml");
	navigationDocument.pushDocument(d);
}

function performAction(action, p) {
	var re = /RunPlugin\(plugin:\/\/(.*)\/\?(.*)\)/;
	var result = re.exec(action);
	if (result != null) {
		var plugin = result[1];
		var query = result[2];
		catalog(btoa(plugin), btoa("plugin://"+plugin+"/?"+query));
		return;
	}
	
	re = /RunPlugin\((.*)\)/;
	var result = re.exec(action);
	if (typeof p != "undefined" && result != null) {
		var query = result[1];
		catalog(btoa(p), btoa(query));
		return;
	}
	
	re = /ItemInfo\((.*)\)/;
	var result = re.exec(action);
	if (result != null) {
		var info = JSON.parse(result[1]);
		showInfoDialog(info);
		return;
	}
}
