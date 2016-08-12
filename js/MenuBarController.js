/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

function MenuBarController(documentLoader, documentURL, loadingDocument) {
    this._documentLoader = documentLoader;
    documentLoader.fetch({
        url: documentURL,
        success: function(menuBarDocument) {
            const menuBarController = this;
            const menuBarElem = menuBarDocument.getElementsByTagName("menuBar").item(0);
            menuBarElem.addEventListener("select", function(event) {
                menuBarController.selectMenuItem(event.target);
            });

            // Pre-load the document for the initial focused menu item or first item,
            // before presenting the menuBarTemplate on navigation stack.
            // NOTE: Pre-loading is optional
            //const initialMenuItemElem = this.findInitialMenuItem(menuBarElem);
            //const initialMenuItemController = this.selectMenuItem(initialMenuItemElem, true, function() {
            //    menuBarController.handleDocument(menuBarDocument, loadingDocument);
            //});
        }.bind(this),
        error: function(xhr) {
            const alertDocument = createLoadErrorAlertDocument(documentURL, xhr, false);
            this.handleDocument(alertDocument, loadingDocument);
        }.bind(this)
    });
}

registerAttributeName('menuBarDocumentURL', MenuBarController);

// Let the DocumentController handle the presentation
MenuBarController.prototype.handleDocument = DocumentController.prototype.handleDocument;

MenuBarController.prototype.findInitialMenuItem = function(menuBarElem) {
    var highlightIndex = 0;
    const menuItemElems = menuBarElem.childNodes;
    for (var i = 0; i < menuItemElems.length; i++) {
        if (menuItemElems.item(i).hasAttribute("autoHighlight")) {
            highlightIndex = i;
            break;
        }
    }
    return menuItemElems.item(highlightIndex);
};

MenuBarController.prototype.selectMenuItem = function(menuItemElem, isInitialItem, doneCallback) {
    const menuBarElem = menuItemElem.parentNode;
    const menuBarFeature = menuBarElem.getFeature("MenuBarDocument");
    const existingDocument = menuBarFeature.getDocument(menuItemElem);

    if (!existingDocument) {
        const controllerOptions = resolveControllerFromElement(menuItemElem);
        if (controllerOptions) {
            if (!isInitialItem) {
                menuBarFeature.setDocument(createLoadingDocument(), menuItemElem);
            }
            const controllerClass = controllerOptions.type;
            const documentURL = controllerOptions.url;
            const controller = new controllerClass(this._documentLoader, documentURL);
            controller.handleDocument = function(document) {
                if (isInitialItem) {
                    menuBarFeature.setDocument(document, menuItemElem);
                } else {
                    // Force timeout to convey intent of displaying loading while the content is being loaded from server
                    setTimeout(function() {
                        // Override the presentation of controller since this controller is child of menuBar and doesn't get pushed on the navigation stack
                        menuBarFeature.setDocument(document, menuItemElem);
                    }, 1000);
                }
                doneCallback && doneCallback();
            };
        }
    }
};
