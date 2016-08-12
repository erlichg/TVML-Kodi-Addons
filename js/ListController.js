/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

function ListController(documentLoader, documentURL, loadingDocument) {
    DocumentController.apply(this, arguments);
}

registerAttributeName('listDocumentURL', ListController);

ListController.prototype.handleDocument = DocumentController.prototype.handleDocument;

ListController.prototype.handleEvent = DocumentController.prototype.handleEvent;

ListController.prototype.setupDocument = function(document) {
    DocumentController.prototype.setupDocument.call(this, document);

    const listElem = document.getElementsByTagName('list').item(0);
    const selectorElem = this.findSelectorElement(document);

    if (selectorElem) {
        selectItem(selectorElem.firstChild);
        selectorElem.addEventListener('highlight', function(event) {
            selectItem(event.target);
        });
    }

    function selectItem(selectedElem) {
        clearResults();
        const sectionElem = document.createElement('section');
        const newItemsCount = selectedElem.getAttribute("numberOfItemsToCreate");
        for (var i = 1, lockupElem; i <= newItemsCount; i++) {
            lockupElem = createResultLockup(i);
            sectionElem.appendChild(lockupElem);
        }
        listElem.appendChild(sectionElem);
    }
    function clearResults() {
        const sectionElems = document.getElementsByTagName('section');
        for (var i = sectionElems.length - 1, elem; i >= 0; i--) {
            elem = sectionElems.item(i);
            elem.parentNode.removeChild(elem);
        }
    }
    function createResultLockup(i) {
        const lockupElem = document.createElement("listItemLockup");
        const titleElem = document.createElement("title");
        titleElem.textContent = 'Title ' + i;
        lockupElem.appendChild(titleElem);
        return lockupElem;
    }
};

ListController.prototype.findSelectorElement = function(document) {
    const tumblerBarElems = document.getElementsByTagName('tumblerBar');
    if (tumblerBarElems.length) {
        return tumblerBarElems.item(0);
    }
    const segmentBarElems = document.getElementsByTagName('segmentBar');
    if (segmentBarElems.length) {
        return segmentBarElems.item(0);
    }
};
