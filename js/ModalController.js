/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information
*/

function ModalController(documentLoader, documentURL) {
    DocumentController.apply(this, arguments);
}

// Prevent the DocumentController to display loadingTemplate
ModalController.preventLoadingDocument = true;

registerAttributeName('modalDocumentURL', ModalController);

ModalController.prototype.setupDocument = DocumentController.prototype.setupDocument;

ModalController.prototype.handleDocument = function(document) {
    navigationDocument.presentModal(document);
};

ModalController.prototype.handleEvent = function(event) {
    // Add necessary code to handle events for elements in Alerts
    navigationDocument.dismissModal();
};