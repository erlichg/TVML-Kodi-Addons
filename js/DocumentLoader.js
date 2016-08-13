/*
Copyright (C) 2016 Apple Inc. All Rights Reserved.
See LICENSE.txt for this sample’s licensing information

Abstract:
This class handles the loading of resources from the network
*/


function DocumentLoader(baseURL) {
    // Bind callback methods to current context
    this.prepareURL = this.prepareURL.bind(this);
    this.prepareElement = this.prepareElement.bind(this);
    this.responses = [];
    // Validate arguments
    if (typeof baseURL !== "string") {
        throw new TypeError("DocumentLoader: baseURL argument must be a string.");
    }
    this.baseURL = baseURL;
}


/*
 * Helper method to request templates from the server
 */
DocumentLoader.prototype.fetch = function(options) {
    if (typeof options.url !== "string") {
        throw new TypeError("DocumentLoader.fetch: url option must be a string.");
    }    
    // Cancel the previous request if it is still in-flight.
    //if (options.concurrent !== true) {
    //    this.cancelFetch();
    //}
    // Parse the request URL
    const docURL = this.prepareURL(options.url);
    const xhr = new XMLHttpRequest();    
    xhr.open("GET", docURL);
    xhr.responseType = "document";
    xhr.onload = function() {
	    if (xhr.status == 202) {
		    var singleVideo = new MediaItem('video', xhr.responseText);
			var videoList = new Playlist();
			videoList.push(singleVideo);
			var myPlayer = new Player();
			myPlayer.playlist = videoList;
			myPlayer.play();
			myPlayer.addEventListener("stateDidChange", function(e) {  
				if(e.state == "end") {
					options.abort();
      			}
    		}.bind(this), false);
    	} else if(xhr.status == 203) {
			try {
				var message = JSON.parse(xhr.responseText);
				console.log("Got messsage: "+xhr.responseText);				
				this.alertDocument = null;
				switch(message.type) {
				case "inputdialog":
					var dialog = createInputDialog(message.title, message.description, {id:"gg",placeholder:"write any text here"}, {text:"OK"});
					var text = dialog.getElementById("gg");
					dialog.addEventListener("select", function() {
						var keyboard = text.getFeature('Keyboard');
						var answer = keyboard.text;
						this.responses.push({id:message.id,response:answer});
						navigationDocument.removeDocument(dialog);
					}.bind(this));
					navigationDocument.pushDocument(dialog);
					break;
				case "progressdialog":
					console.log("creating progress dialog");
					var dialog = createProgressDialog(message.title, message.line1, message.line2, message.line3, 'Progress: 0%');
					navigationDocument.pushDocument(dialog);
					this.isprogresscanceled = false;
					this.progressDialog = dialog;
					dialog.addEventListener("disappear", function() {
						this.isprogresscanceled = true;
						this.progressDialog = null;
					}.bind(this));
					this.responses.push({id:message.id, response:'OK'})
					break;
				case "updateprogress":
					console.log("updating progress");
					if(typeof this.progressDialog != "undefined" && !this.isprogresscanceled) {
						var dialog = this.progressDialog;
						try {	
							dialog.getElementById("line1").textContent = message.line1;
							dialog.getElementById("line2").textContent = message.line2;
							dialog.getElementById("line3").textContent = message.line3;	
							dialog.getElementById("progress").textContent = 'Progress: '+message.percent+'%';							
						} catch(e) {
							console.log("ERROR: "+e);
						}
					}
					this.responses.push({id:message.id, response:'OK'})
					break;
				case "isprogresscanceled":
					var b = typeof this.progressDialog != "undefined" && this.isprogresscanceled;
					console.log("answering to isprogresscanceled with: "+b);
					this.responses.push({id:message.id, response:b});
					break;
				case "closeprogress":
					console.log("removing progress dialog");
					navigationDocument.removeDocument(this.progressDialog);
					this.responses.push({id:message.id, response:'OK'})
					break;
				case "selectdialog":
					console.log("creating select dialog");
					var dialog = createSelectDialog(message.title, message.list);
					navigationDocument.pushDocument(dialog);
					break;
				case "play":
					console.log("creating player");
					var singleVideo = new MediaItem('video', message.url);
					var videoList = new Playlist();
					videoList.push(singleVideo);
					var myPlayer = new Player();
					myPlayer.playlist = videoList;
					myPlayer.play();
					this.isplaying = true;
					myPlayer.addEventListener("stateDidChange", function(e) {  
						if(e.state == "end") {
							this.isplaying = false;
							navigationDocument.popDocument();
      					}
    				}.bind(this), false);
    				this.responses.push({id:message.id, response:'OK'})
    				break;
    			case "isplaying":
    				var b = typeof this.isplaying != "undefined" && this.isplaying;
					console.log("answering to isplaying with: "+b);
					this.responses.push({id:message.id, response:b})
					break;
				}
			} catch(err) {
				console.log("unable to parse message"+err);
			}
		} else if(xhr.status == 204) {
			//no message
		} else if(xhr.status == 205) {
			console.log('sent response')	
	    } else if(xhr.status == 206) {
		    options.abort();
	    } else {
        	const responseDoc = xhr.response;
        	if (typeof options.initial == "boolean" && options.initial) {
	        	console.log("registering event handlers");
				responseDoc.addEventListener("disappear", function() {
					if(navigationDocument.documents.length==1) {
						//if we got here than we've exited from the web server since the only page (root) has disappeared
						stopTimer(this);
						App.onExit({});
					}
				}.bind(this));				
    		}
			this.prepareDocument(responseDoc);
			if (typeof options.success === "function") {
            	options.success(responseDoc);
        	} else {
            	navigationDocument.pushDocument(responseDoc);
        	}
        }
    }.bind(this);
    xhr.onerror = function() {
        if (typeof options.error === "function") {
            options.error(xhr);
        } else {
            const alertDocument = createLoadErrorAlertDocument(docURL, xhr, true);
            navigationDocument.presentModal(alertDocument);
        }
    };
    xhr.timeout = 0;
    xhr.send();
    // Preserve the request so it can be cancelled by the next fetch
    if (options.concurrent !== true) {
        this._fetchXHR = xhr;
    }
};

/*
 * Helper method to cancel a running XMLHttpRequest
 */
DocumentLoader.prototype.cancelFetch = function() {
	console.log("Aborting fetch");
    const xhr = this._fetchXHR;
    if (xhr && xhr.readyState !== XMLHttpRequest.DONE) {
        xhr.abort();
    }
    delete this._fetchXHR;
};

/*
 * Helper method to convert a relative URL into an absolute URL
 */
DocumentLoader.prototype.prepareURL = function(url) {
    // Handle URLs relative to the "server root" (baseURL)
    if (url.indexOf("/") === 0) {
        url = this.baseURL + url.substr(1);
    }
    return url;
};

/*
 * Helper method to mangle relative URLs in XMLHttpRequest response documents
 */
DocumentLoader.prototype.prepareDocument = function(document) {
    traverseElements(document.documentElement, this.prepareElement);
    if (document.documentElement.getElementsByTagName("formTemplate").length != 0) {
	    var text = document.documentElement.getElementsByTagName("textField")[0];
	    var id = text.getAttribute("id");	    
		dialog.addEventListener("select", function() {
			var keyboard = text.getFeature('Keyboard');
			var answer = keyboard.text;			
			navigationDocument.removeDocument(dialog);
			this.fetch({
				url: this.baseURL + "response/" + id + "/" + answer
			});
		}.bind(this));
    }
};

/*
 * Helper method to mangle relative URLs in DOM elements
 */
DocumentLoader.prototype.prepareElement = function(elem) {
    if (elem.hasAttribute("src")) {
        const rawSrc = elem.getAttribute("src");
        const parsedSrc = this.prepareURL(rawSrc);
        elem.setAttribute("src", parsedSrc);
    }
    if (elem.hasAttribute("srcset")) {
        // TODO Prepare srcset attribute
    }
}

/**
 * Convenience function to iterate and recurse through a DOM tree
 */
function traverseElements(elem, callback) {
    callback(elem);
    const children = elem.children;
    for (var i = 0; i < children.length; ++i) {
	    traverseElements(children.item(i), callback);
    }
}

