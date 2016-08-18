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
		    var msg = JSON.parse(xhr.responseText)
		    console.log("got message: " + xhr.responseText);
		    var singleVideo = new MediaItem(msg['type'], msg['url']);
			var videoList = new Playlist();
			videoList.push(singleVideo);
			var myPlayer = new Player();			
			myPlayer.playlist = videoList;
			var overlayDocument = createSubtitleDocument();
			var subtitle = overlayDocument.getElementsByTagName("text").item(0);
			myPlayer.play();
			myPlayer.addEventListener("timeDidChange", function(info) {
				console.log("timeDidChange");
				subtitle.textContent = "timeDidChange "+info.time;
			}, {"interval":1});
			myPlayer.addEventListener("stateDidChange", function(e) {  
				if(e.state == "end") {
					options.abort();
					this.fetch({
						url:msg['stop'],
						abort: function() {
							//do nothing
						}
					});
      			} else if(e.state == "playing") {
	      			console.log("attaching overlay");
	      			myPlayer.overlayDocument = overlayDocument;	      			
      			}
    		}.bind(this), false);
		} else if(xhr.status == 204) {
			//no message
		} else if(xhr.status == 205) {
			console.log('sent response')
	    } else if(xhr.status == 206) {
		    options.abort();
		} else if(xhr.status == 208) {
			const responseDoc = xhr.response;
			this.prepareDocument(responseDoc);
			options.success(responseDoc, true);
	    } else {
        	const responseDoc = xhr.response;
        	if (typeof options.initial == "boolean" && options.initial) {
	        	console.log("registering event handlers");
				responseDoc.addEventListener("disappear", function() {
					if(navigationDocument.documents.length==1) {
						//if we got here than we've exited from the web server since the only page (root) has disappeared
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
    if (document.documentElement.getElementsByTagName("formTemplate").length != 0) { //input dialog
	    var text = document.getElementById("text");
	    var id = document.documentElement.getElementsByTagName("formTemplate").item(0).getAttribute("msgid");	
	    var ans = false;    
		document.addEventListener("select", function() {
			ans = true;
			var keyboard = text.getFeature('Keyboard');
			var answer = keyboard.text;	
			//navigationDocument.removeDocument(document); //remove the document	
			//navigationDocument.dismissModal();
			//setTimeout(function() {
				this.fetch({
					url: "/response/" + id + "/" + btoa(answer),
					abort: function() {
						
					}
				});
			//}.bind(this), 100);				
			
		}.bind(this));
		document.addEventListener("unload", function() {
			if (!ans) {
				this.fetch({
				url: "/response/" + id,
				abort: function() {
					//do nothing
				},
				error: function(xhr) {
					//do nothing
				}
			});
			}
		}.bind(this));
    } else if (typeof document.getElementById("progress")!="undefined") { //progress dialog
	    var progress = document.getElementById("progress");
	    var url = progress.getAttribute("documentURL");
	    var id = progress.getAttribute("msgid");
	    this.fetch({
			url: url,
			success: function(responseDoc) {
				try {
					navigationDocument.replaceDocument(responseDoc, document);
				} catch (err) {
					this.fetch({
					url: "/response/" + id,
					abort: function() {
						//do nothing
					},
					error: function(xhr) {
						//do nothing
					}
				});
				}
			}.bind(this),
			abort: function() {
				try {
					navigationDocument.removeDocument(document); //remove the document
				} catch (err) {
					this.fetch({
					url: "/response/" + id,
					abort: function() {
						//do nothing
					},
					error: function(xhr) {
						//do nothing
					}
				});
				}
			}.bind(this)
		});
    } else if (typeof document.getElementById("player")!="undefined") { //player
	    var m = document.getElementById("player");
	    var singleVideo = new MediaItem(m.getAttribute('type'), m.getAttribute('url'));
		var videoList = new Playlist();
		videoList.push(singleVideo);
		var myPlayer = m.getFeature('Player');			
		myPlayer.playlist = videoList;
		var subtitle = m.getElementsByTagName("text").item(0);
		myPlayer.play();
		myPlayer.addEventListener("timeDidChange", function(info) {
			console.log("timeDidChange");
			subtitle.textContent = "timeDidChange "+info.time;
		}, {"interval":1});
		myPlayer.addEventListener("stateDidChange", function(e) {  
			if(e.state == "end") {
				options.abort();
				this.fetch({
					url:msg['stop'],
					abort: function() {
						//do nothing
					}
				});
      		} else if(e.state == "playing") {
	    		console.log("attaching overlay");
	    		myPlayer.overlayDocument = overlayDocument;	      			
      		}
    	}.bind(this), false);
    }
    traverseElements(document.documentElement, function(elem) {
	   if (elem.hasAttribute("notify")) {
		   var url = elem.getAttribute("notify");
		   elem.addEventListener("select", function() {
			   this.fetch({
					url: url,
					abort: function() {
						navigationDocument.removeDocument(document); //remove the document
					},
					error: function(xhr) {
						//do nothing
					}				
		   		});
	   		}.bind(this)) 
	   	}
    }.bind(this));
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

