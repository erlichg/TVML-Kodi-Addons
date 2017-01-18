/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

function prepareSearchDocument(document) {
    // Obtain references to some useful elements in the searchTemplate
    const searchTemplateElem = document.getElementsByTagName('searchTemplate').item(0);
    const searchFieldElem = document.getElementsByTagName('searchField').item(0);
    const separatorElem = document.getElementsByTagName('separator').item(0);
    const messageElem = document.getElementById("message");
    const suggestionsElem = document.getElementById("suggestions");
    const defaultResultsElem = document.getElementById("defaultResults");
    const resultsListElem = document.getElementById("resultsList");
    const resultsGridContainerElem = document.getElementById("resultsGridContainer");
    const resultsSectionElem = document.getElementById("resultsSection");

    // Clean up the document for initial presentation
    var resultsContainerElem = resultsGridContainerElem;
    
    // Show the new results container in the collectionList
    //resultsListElem.appendChild(resultsContainerElem);
    //resultsContainerElem.appendChild(resultsSectionElem);
    toggleDefaultResults(true);	

	const searchResultsCache = [];
    const searchKeyboard = searchFieldElem.getFeature("Keyboard");
    // Register an event handler for search input changes
    searchKeyboard.onTextChange = performSearchRequest;

    
    // Register an event handler for search suggestions selection
    suggestionsElem.addEventListener("select", function(event) {
        const selectedElement = event.target;
        const searchValue = selectedElement.getAttribute("value");
        searchKeyboard.text = searchValue;
        performSearchRequest();
    });

    // Register an event handler for search result selection
/*
    resultsSectionElem.addEventListener("select", function(event) {
        const selectedElement = event.target;
        handleSelectionForItem(selectedElement);
    });

    resultsSectionElem.addEventListener("holdselect", function(event) {
        const selectedElement = event.target;
        handleHoldSelectionForItem(selectedElement);
    });
    

    defaultResultsElem.addEventListener("select", function(event) {
	    const selectedElement = event.target;
        handleSelectionForItem(selectedElement);
    });

    defaultResultsElem.addEventListener("holdselect", function(event) {
	    const selectedElement = event.target;
        handleHoldSelectionForItem(selectedElement);
    });
*/
    /*
     * Show or hide the message in the search body.
     * Sets the content of the message if it is to be shown.
     */
    function toggleSearchMessage(bool, message) {
        if (bool) {
            // Set the message text
            if (message) {
                messageElem.textContent = message;
            }
            // Show the message if it's hidden
            if (!messageElem.parentNode) {
                searchTemplateElem.appendChild(messageElem);
            }
            toggleModeButtons(false);
        } else {
            // Hide the message if it's visible
            if (messageElem.parentNode) {
                searchTemplateElem.removeChild(messageElem);
            }
            toggleModeButtons(true);
        }
    }

    function toggleSearchSuggestions(bool) {
        if (bool) {
            // Show the suggestions if they're hidden
            if (!suggestionsElem.parentNode) {
                searchTemplateElem.appendChild(suggestionsElem);
            }
            toggleSearchMessage(false);
            toggleModeButtons(false);
        } else {
            // Hide the suggestions if they're visible
            if (suggestionsElem.parentNode) {
                searchTemplateElem.removeChild(suggestionsElem);
            }
            toggleModeButtons(true);
        }
    }

    function toggleDefaultResults(bool) {
        if (bool) {
            // Swap the default results in for the container
            if (resultsContainerElem.parentNode) {
                resultsListElem.removeChild(resultsContainerElem);
                resultsListElem.appendChild(defaultResultsElem);
            }
            toggleSearchMessage(false);
            toggleSearchSuggestions(false);
            toggleModeButtons(false);
        } else {
            // Swap the default results out and the container in
            if (!resultsContainerElem.parentNode) {
                resultsListElem.removeChild(defaultResultsElem);
                resultsListElem.appendChild(resultsContainerElem);
            }
            toggleModeButtons(true);
        }
    }

    function toggleModeButtons(bool) {
        if (bool) {
            if (!separatorElem.parentNode) {
                searchTemplateElem.appendChild(separatorElem);
            }
        } else {
            if (separatorElem.parentNode) {
                searchTemplateElem.removeChild(separatorElem);
            }
        }
    }

    function performSearchRequest() {
        // Strip leading, trailing, and multiple whitespaces from the query
        const searchText = new RegExp(searchKeyboard.text.trim().replace(/\s+/g, " "), "gi");

        // Show the initial message and stop if there's no search query
        if (searchText.length === 0) {
            toggleDefaultResults(true);
            return;
        }
		const searchResults = [];
		var lockups = defaultResultsElem.getElementsByTagName("lockup");
        for (var i=0; i<lockups.length; i++) {
	        var elem = lockups.item(i);
	        if (searchText.test(elem.getElementsByTagName("title").item(0).textContent)) {
		        searchResults.push(elem);
	        } else if (searchText.test(elem.getElementsByTagName("placeholder").item(0).textContent)) {
	            searchResults.push(elem);
	        }
        }
        showSearchResponse(searchKeyboard.text, searchResults);
    }

    /*
     * Show a generic error message in the search body
     */
    function showSearchError() {
        toggleSearchMessage(true, "An error occurred during your search.");
    }

    /*
     * Parse the XHR response and show the results or a message
     */
    function showSearchResponse(text, searchResults) {
        // Prepare the document for new search results
        toggleDefaultResults(false);
        toggleSearchSuggestions(false);
        clearSearchResults();

        // Show the results (or lack thereof)
        if (searchResults.length > 0) {
            appendSearchResults(searchResults);
            toggleSearchMessage(false);
        } else {
            if (text.length > 3) {
                toggleSearchMessage(true, `No results for ${text}.`);
            } else {
                toggleSearchSuggestions(true);
            }
        }
    }

    /*
     * Empty the results cache and remove all results lockup elements.
     */
    function clearSearchResults() {
        searchResultsCache.length = 0;
        // Remove all existing search results
        while (resultsSectionElem.firstChild) {
            resultsSectionElem.removeChild(resultsSectionElem.firstChild);
        }
    }

    /*
     * Create lockup elements for the search results and cache
     * the data to be referenced by the selection handler.
     */
    function appendSearchResults(results) {
        const startIndex = searchResultsCache.length;
        // Create new lockups for the results
        results.forEach(function(item, index) {
            resultsSectionElem.appendChild(item.cloneNode(true));
            // Add the item to the search results cache
            searchResultsCache.push(item);
        });
    }


    return document;
}
