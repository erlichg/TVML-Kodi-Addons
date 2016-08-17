//# sourceURL=application.js

/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information

Abstract:
This is the entry point to the application and handles the initial loading of required JavaScript files.

This application uses custom attributes specified in the markup to define document URLs to be loaded on select / play event.
These attributes are mapped to a corresponding controller class defined in this application, which are responsible for handling 
the life-cycle and events of that document. 

The following attributes are used in this application:
- "documentURL" maps to DocumentController: this is the default controller that is used to fetch and push a document on the navigation stack.

- "menuBarDocumentURL" maps to MenuBarController: the menuBarTemplate itself is pushed on navigation stack (hence subclasses from DocumentController),
        but this controller manages the document controllers associated with the menu items of the template.

- "modalDocumentURL" maps to ModalController: This controller is similar to DocumentController but presents the 
        document as modal.

- "searchDocumentURL" maps to SearchController: Handles the search template. This example demonstrates a default shelf
        , suggestions list and search results from iTunes store. The default results and suggestions are mocked.

- "listDocumentURL" maps to ListController: Handles the list with segment and tumbler elements.

- "slideshowImageURLs" maps to SlideshowController: Handles the presentation of slideshow of photos specified by the 
        attribute.
*/

/**
 * @description The onLaunch callback is invoked after the application JavaScript
 * has been parsed into a JavaScript context. The handler is passed an object
 * that contains options. These options are defined in the Swift or objective-c client code.
 * Options can be used to communicate data and state information to your JavaScript code.
 *
 * The location attribute is automatically added to the options object and represents
 * the URL that was used to retrieve the application JavaScript.
 */
 
var documentLoader;
App.onLaunch = function(options) {
    // Determine the base URL for remote server fetches from launch options, which will be used to resolve the URLs
    // in XML files for this app.
    const baseURL = options.baseURL || (function(appURL) {
        return appURL.substr(0, appURL.lastIndexOf("/")) + "/../";
    })(options.location);

    // Specify all the URLs for helper JavaScript files
    const helperScriptURLs = [
        "DocumentLoader",
        "DocumentController",
        "ListController",
        "MenuBarController",
        "ModalController",
        "SearchController",
        "SlideshowController"
    ].map(function(moduleName) {
        return `${baseURL}js/${moduleName}.js`;
    });

    // Show a loading spinner while additional JavaScript files are being evaluated
    const loadingDocument = createLoadingDocument();
    navigationDocument.pushDocument(loadingDocument);

    // evaluateScripts is responsible for loading the JavaScript files neccessary
    // for this app to run. It can be used at any time in your apps lifecycle.
    evaluateScripts(helperScriptURLs, function(scriptsAreLoaded) {
        if (scriptsAreLoaded) {
            // Instantiate the DocumentLoader, which will be used to fetch and resolve URLs from the fecthed XML documents.
            // This instance is passed along to subsequent DocumentController objects.
            documentLoader = new DocumentLoader(baseURL);
            //const startDocURL = baseURL + "templates/Index.xml";
            const startDocURL = baseURL + "main";
            // Instantiate the controller with root template. The controller is passed in the loading document which
            // was pushed while scripts were being evaluated, and controller will replace it with root template once
            // fetched from the server.
            var rootDoc = new DocumentController(documentLoader, startDocURL, loadingDocument, true);			
        } else {
            // Handle error cases in your code. You should present a readable and user friendly
            // error message to the user in an alert dialog.
            const alertDocument = createEvalErrorAlertDocument();
            navigationDocument.replaceDocument(alertDocument, loadingDocument);
            throw new EvalError("TVMLCatalog application.js: unable to evaluate scripts.");
        }
    });
};

/*
	This is exit point of the app. it is called when the user exits (i.e. presses 'menu' back from the root document)
*/
App.onExit = function(options) {
	
}

/*
	This is called when the app gois to background
*/
App.onSuspend = function(options) {

}

/*
	This is called when app returns from background
*/
App.onResume = function(options) {
}

/*
	This is called when app receives memory warning. If ignored, the app will be exited forcefully
*/
App.onMemoryWarning = function(options) {
	
}

/**
 * Convenience function to create a TVML loading document with a specified title.
 */
function createLoadingDocument(title) {
    // If no title has been specified, fall back to "Loading...".
    title = title || "Loading...";

    const template = `<?xml version="1.0" encoding="UTF-8" ?>
        <document>
            <loadingTemplate>
                <activityIndicator>
                    <title>${title}</title>
                </activityIndicator>
            </loadingTemplate>
        </document>
    `;
    return new DOMParser().parseFromString(template, "application/xml");
}

/**
 * Convenience function to create a TVML alert document with a title and description.
 */
function createAlertDocument(title, description, isModal) {
    // Ensure the text color is appropriate if the alert isn't going to be shown modally.
    const textStyle = (isModal) ? "" : "color: rgb(0,0,0)";

    const template = `<?xml version="1.0" encoding="UTF-8" ?>
        <document>
            <alertTemplate>
                <title style="${textStyle}">${title}</title>
                <description style="${textStyle}">${description}</description>
            </alertTemplate>
        </document>
    `;
    return new DOMParser().parseFromString(template, "application/xml");
}

/**
 * Convenience function to create a TVML alert document with a title and description.
 */
function createDescriptiveAlertDocument(title, description) {
    const template = `<?xml version="1.0" encoding="UTF-8" ?>
        <document>
            <descriptiveAlertTemplate>
                <title>${title}</title>
                <description>${description}</description>
            </descriptiveAlertTemplate>
        </document>
    `;
    return new DOMParser().parseFromString(template, "application/xml");
}

/**
 * Convenience function to create a TVML alert for failed evaluateScripts.
 */
function createEvalErrorAlertDocument() {
    const title = "Evaluate Scripts Error";
    const description = [
        "There was an error attempting to evaluate the external JavaScript files.",
        "Please check your network connection and try again later."
    ].join("\n\n");
    return createAlertDocument(title, description, false);
}


/**
 * Convenience function to create a TVML alert for a failed XMLHttpRequest.
 */
function createLoadErrorAlertDocument(url, xhr, isModal) {
    const title = "Communication error";
    const description = "Failed to load page.\nThis could mean the server had a problem, or the request dialog timed out.\nPlease try again";
    return createAlertDocument(title, description, isModal);
}

/**
 * Convenience function to create a TVML dialog
 */
 function createInputDialog(title, description, textfield, button) {
	 var template = `<?xml version="1.0" encoding="UTF-8" ?>
        <document>
        `;
	 template+=`<formTemplate>`;
	 template+=`<title>${title}</title>
                <description>${description}</description>                
                `;
	     template+=`<textField id="${textfield.id}">${textfield.placeholder}</textField>`;     
     if(typeof button !== "undefined") {
		 template+=`<footer>`;
		 template+=`<button>
	     				<text>${button.text}</text>
	     			</button>
	     			`;
		 template+=`</footer>`;
		 
     }
	 template+=`</formTemplate>`;
	 template+=`</document>`;
    return new DOMParser().parseFromString(template, "application/xml");
 }
 
 function createProgressDialog(title, line1, line2, line3, progress) {
	 var template = `<document>
    <head>
		<style>
			.desc {
				font-size: 35;
                text-align: center;
			}
        </style>
	</head>
	<listTemplate>
        <banner>
	        <title id="title">${title}</title>
            <description id="line1" class="desc">${line1}</description>
            <description id="line2" class="desc">${line2}</description>
            <description id="line3" class="desc">${line3}</description>
		    <description id="progress" class="desc">${progress}</description>
		    <activityIndicator></activityIndicator>
        </banner>
	</listTemplate>
</document>`;
	return new DOMParser().parseFromString(template, "application/xml");
 }
 
 function createSubtitleDocument() {
	 var template = `<?xml version="1.0" encoding="UTF-8" ?>
<!--
 Copyright (C) 2016 Apple Inc. All Rights Reserved.
 See LICENSE.txt for this sample’s licensing information
 -->
<document>
	<stackTemplate onload="setupMediaContent(event.target)">
		<banner>
			<title>Always Playing Embedded Videos</title>
		</banner>

		<collectionList style="margin: 100 0 0;">
			<shelf style="tv-interitem-spacing: 50;" onselect="presentVideo(event.target)">
				<section>
					<lockup>
						<mediaContent mediaContent="http://p.events-delivery.apple.com.edgesuite.net/15pijbnaefvpoijbaefvpihb06/m3u8/hls_vod_mvp.m3u8" playbackMode="always">
							<img src="http://images.apple.com/apple-events/static/apple-events/apple-events-index/pastevents/june2015/hero_image_large.jpg" aspectFill="true" width="845" height="475"/>
						</mediaContent>
					</lockup>
					<lockup>
						<mediaContent mediaContent="http://p.events-delivery.apple.com.edgesuite.net/1509pijnedfvopihbefvpijlkjb/m3u8/hls_vod_mvp.m3u8" playbackMode="always">
							<img src="http://images.apple.com/apple-events/static/apple-events/apple-events-index/hero/september2015/hero_image_large.jpg" aspectFill="true" width="845" height="475"/>
						</mediaContent>
					</lockup>
				</section>
			</shelf>
		</collectionList>
	</stackTemplate>
</document>`;
	return new DOMParser().parseFromString(template, "application/xml");
 }

