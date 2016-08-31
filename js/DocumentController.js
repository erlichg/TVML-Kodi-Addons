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

function DocumentController(documentLoader, documentURL, loadingDocument, initial) {
    this.handleEvent = this.handleEvent.bind(this);
    this.handleHoldSelect = this.handleHoldSelect.bind(this);
    this._documentLoader = documentLoader;
    documentLoader.fetch({
	    initial: initial,
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
	if (target.hasAttribute("menuURL")) {
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
	}
}

function notify(url) {
	documentLoader.fetch({
		url:url,
		abort: function() {
						
		},
		success: function() {
			
		},
		error: function() {
			
		}
	});
}

function load(url) {
	console.log("loading "+url);
	var loadingDocument = createLoadingDocument();
	navigationDocument.pushDocument(loadingDocument);
	new DocumentController(documentLoader, url, loadingDocument);
}

function saveSettings(addon, settings) {
	console.log("saving settings: "+JSON.stringify(settings));
	var addonsSettings = null;
    if (addonsSettings == null) {
	    addonsSettings = {};
    }
    addonsSettings[addon] = settings;
    localStorage.setItem('addonsSettings', JSON.stringify(addonsSettings));
}

function loadSettings(addon) {
	var addonsSettings = null;
    if (addonsSettings == null) {
	    addonsSettings = "{}";
    }
    console.log('Loaded settings '+addonsSettings);
    addonsSettings = JSON.parse(addonsSettings);
    var addonSettings = addonsSettings[addon];
    if(addonSettings == null) {
	    addonSettings = {};
    }
    return addonSettings;
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
