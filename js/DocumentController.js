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

function DocumentController(documentLoader, documentURL, loadingDocument, initial, data) {
    this.handleEvent = this.handleEvent.bind(this);
    this.handleHoldSelect = this.handleHoldSelect.bind(this);
    this._documentLoader = documentLoader;
    if (typeof initial == "boolean" && initial) {
	    var favs = loadFavourites();
		documentLoader.post({
	    	initial: initial,	    	
        	url: documentURL,
        	data: btoa(JSON.stringify(favs)),
        	success: function(document, isModal) {
        	    // Add the event listener for document
        	    this.setupDocument(document);
        	    // Allow subclass to do custom handling for this document
        	    this.handleDocument(document, loadingDocument, isModal);
        	}.bind(this),
        	error: function(xhr) {
        	    const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
        	    this.handleDocument(alertDocument, loadingDocument);
        	}.bind(this),
        	abort: function() {
	    	    if(loadingDocument) {
			        navigationDocument.removeDocument(loadingDocument);
	    	    }
        	}
    	}); 	       					
    } else if (typeof data != "undefined") {
	    documentLoader.post({
	    	initial: initial,	    	
        	url: documentURL,
        	data: data,
        	success: function(document, isModal) {
        	    // Add the event listener for document
        	    this.setupDocument(document);
        	    // Allow subclass to do custom handling for this document
        	    this.handleDocument(document, loadingDocument, isModal);
        	}.bind(this),
        	error: function(xhr) {
        	    const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
        	    this.handleDocument(alertDocument, loadingDocument);
        	}.bind(this),
        	abort: function() {
	    	    if(loadingDocument) {
			        navigationDocument.removeDocument(loadingDocument);
	    	    }
        	}
    	});
    } else {
    	documentLoader.fetchPost({
		    initial: false,
    	    url: documentURL,
    	    success: function(document, isModal) {
    	        // Add the event listener for document
    	        this.setupDocument(document);
    	        // Allow subclass to do custom handling for this document
    	        this.handleDocument(document, loadingDocument, isModal);
    	    }.bind(this),
    	    error: function(xhr) {
    	        const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
    	        this.handleDocument(alertDocument, loadingDocument);
    	    }.bind(this),
    	    abort: function() {
		        if(loadingDocument) {
			        navigationDocument.removeDocument(loadingDocument);
		        }
    	    }
    	});
    }
}

registerAttributeName('documentURL', DocumentController);

DocumentController.prototype.setupDocument = function(document) {
    document.addEventListener("select", this.handleEvent);
    document.addEventListener("play", this.handleEvent);
    document.addEventListener("holdselect", this.handleHoldSelect);    
};

DocumentController.prototype.handleDocument = function(document, loadingDocument, isModal) {	
    if (loadingDocument && navigationDocument.documents.indexOf(loadingDocument)!=-1) {
	    if (typeof isModal == "undefined") {   
        	navigationDocument.replaceDocument(document, loadingDocument);
        } else {
	        //navigationDocument.removeDocument(loadingDocument);
	        navigationDocument.presentModal(document);
	        document.addEventListener("unload", function(e) {
		       navigationDocument.removeDocument(loadingDocument); 
	        });
	        document.addEventListener("select", function(e) {
		       navigationDocument.dismissModal();
	        });
        }     
    } else {
	    if (typeof isModal == "undefined") { 
        	navigationDocument.pushDocument(document);
        } else {
	        navigationDocument.presentModal(document);
	        document.addEventListener("select", function(e) {
		       navigationDocument.dismissModal();
	        });
        }
    }
};

DocumentController.prototype.handleEvent = function(event) {
    const target = event.target;

    const controllerOptions = resolveControllerFromElement(target);
    if (controllerOptions) {
        const controllerClass = controllerOptions.type;
        const documentURL = controllerOptions.url;
        var loadingDocument;
        if (!controllerClass.preventLoadingDocument) {
            loadingDocument = createLoadingDocument();
            navigationDocument.pushDocument(loadingDocument);
        }
        // Create the subsequent controller based on the atribute and its value. Controller would handle its presentation.
        new controllerClass(this._documentLoader, documentURL, loadingDocument);
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

function notify(url) {
	console.log("notify: "+url);
	documentLoader.fetchPost({
		url:url,
		abort: function() {
						
		},
		success: function() {
			
		},
		error: function() {
			
		}
	});
}

function load(url, initial) {
	console.log("loading "+url);
	if (typeof initial == "boolean" && initial) {
		navigationDocument.clear();
	}
	var loadingDocument = createLoadingDocument();
	navigationDocument.pushDocument(loadingDocument);	
	new DocumentController(documentLoader, url, loadingDocument, initial);
}

function post(url, data) {
	console.log("posting "+url);
	var loadingDocument = createLoadingDocument();
	navigationDocument.pushDocument(loadingDocument);
	new DocumentController(documentLoader, url, loadingDocument, false, data);
	
}

function saveSettings(addon, settings) {
	console.log("saving settings: "+JSON.stringify(settings));
	localStorage.setItem(addon, JSON.stringify(settings));
}

function loadSettings(addon) {
	var addonsSettings = localStorage.getItem("addonsSettings");
	if (addonsSettings != null) {
	    addonsSettings = JSON.parse(addonsSettings);
	    for (var a in addonsSettings) {
		    localStorage.setItem(a, JSON.stringify(addonsSettings[a]));		    
	    }
	    localStorage.removeItem("addonsSettings");
    }
	var addonSettings = localStorage.getItem(addon);
    if(addonSettings == null) {
	    addonSettings = "{}";
    }
    try {
	    addonSettings = JSON.parse(addonSettings);
    } catch (e) {
	    addonSettings = {};
    }
    console.log('Loaded addon settings '+JSON.stringify(addonSettings));
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

function saveFavourites(favs) {
	localStorage.setItem('favourites', JSON.stringify(favs));
}

function addToFavourites(addon) {
	var favs = loadFavourites();
	favs.push(addon);
	saveFavourites(favs);
}

function removeFromFavourites(addon) {
	var favs = loadFavourites();
	var index = favs.indexOf(addon);
	if (index > -1) {
    	favs.splice(index, 1);
	}
	saveFavourites(favs);
}

function removeAddon(addon) {
	post('/removeAddon', btoa(addon));
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

function showSelectDialog(title, choices, index, callback) {
	var template=`<?xml version="1.0" encoding="UTF-8" ?>
  <document>
	<head>
	  <style>
	  </style>
	  <banner>
         <title>${title}</title>
      </banner>
	</head>
	<listTemplate>
	  <list>
		  <section>`;
	for (var item in choices) {
		template = template + `<listItemLockup>										
				 	<title>${choices[item]}</title>				 					 	
				</listItemLockup>`;
	}
	template = template +`</section>
	  </list>
	</listTemplate>
  </document>`;
  	var dialog = new DOMParser().parseFromString(template, "application/xml");
	var sent_answer = false;
	dialog.addEventListener("select", function(event) {
		var ans = event.target.childNodes.item(0).textContent;
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
		load("/catalog/"+btoa(plugin)+"/"+btoa(query));	
		return;
	}
	
	re = /RunPlugin\((.*)\)/;
	var result = re.exec(action);
	if (typeof p != "undefined" && result != null) {
		var query = result[1];
		load("/catalog/"+btoa(p)+"/"+btoa(query));	
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
