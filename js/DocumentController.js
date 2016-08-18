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
		var loadingDocument;
        if (!DocumentController.preventLoadingDocument) {
            loadingDocument = createLoadingDocument();
            navigationDocument.pushDocument(loadingDocument);
        }
        // Create the subsequent controller based on the atribute and its value. Controller would handle its presentation.
        new DocumentController(this._documentLoader, documentURL, loadingDocument);
	}
}
