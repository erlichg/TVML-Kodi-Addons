/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

function prepareMenuBarDocument(menuBarDocument) {
	const menuBarElem = menuBarDocument.getElementsByTagName("menuBar").item(0);
	menuBarElem.addEventListener("select", function(event) {
		menuBarController.selectMenuItem(event.target);
	});

	// Pre-load the document for the initial focused menu item or first item,
	// before presenting the menuBarTemplate on navigation stack.
	// NOTE: Pre-loading is optional
	const initialMenuItemElem = this.findInitialMenuItem(menuBarElem);
	const initialMenuItemController = this.selectMenuItem(initialMenuItemElem, true, function() {
	    //menuBarController.handleDocument(menuBarDocument, loadingDocument);
	});
        

	function findInitialMenuItem(menuBarElem) {
    	var highlightIndex = 0;
		const menuItemElems = menuBarElem.childNodes;
		for (var i = 0; i < menuItemElems.length; i++) {
        	if (menuItemElems.item(i).hasAttribute("autoHighlight")) {
            	highlightIndex = i;
				break;
        	}
    	}
		return menuItemElems.item(highlightIndex);
	}

	function selectMenuItem(menuItemElem, isInitialItem, doneCallback) {
    	const menuBarElem = menuItemElem.parentNode;
    	const menuBarFeature = menuBarElem.getFeature("MenuBarDocument");
    	const existingDocument = menuBarFeature.getDocument(menuItemElem);
		
    	if (!existingDocument) {
    	        menuBarFeature.setDocument(document, menuItemElem);
		}
	}
}