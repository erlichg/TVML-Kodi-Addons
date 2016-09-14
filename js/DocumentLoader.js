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

DocumentLoader.prototype.post = function(options) {
	if (typeof options.url !== "string") {
        throw new TypeError("DocumentLoader.fetch: url option must be a string.");
    }
    const docURL = this.prepareURL(options.url);
    const xhr = new XMLHttpRequest();    
    xhr.open("POST", docURL);
    xhr.timeout = 0;
    xhr.onload = function() {
		if (typeof options.success != "undefined") {
			options.success();
		}  
    };
    xhr.onerror = function() {
		if (typeof options.failure != "undefined") {
			options.failure();
		}  
    };
    xhr.send(options.data);
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
	    console.log('got status '+xhr.status);
	    if (xhr.status == 202) {
		    var msg = JSON.parse(xhr.responseText)
/*
		    try {
			    play(msg['url']);
		    } catch (e) {
			    console.log(e);
		    }
*/
		    

		    console.log("got message: " + xhr.responseText);
		    var time;
		    var playCache = localStorage.getItem('playCache');
		    if (playCache == null) {
			    playCache = '{}';
		    }
		    playCache = JSON.parse(playCache);
		    if (playCache[msg['url']] != null) { //if we've played this url before, retrieve it's stop time
			    time = playCache[msg['url']];
		    } else {
			    time = 0;
		    }
		    var singleVideo = new MediaItem(msg['type'], msg['url']);
		    if(msg['image'] != null) {
		    	singleVideo.artworkImageURL = msg['image'];
		    }
		    if(msg['description'] != null) {
		    	singleVideo.description = msg['description'];
		    }
		    if(msg['title'] != null) {
		    	singleVideo.title = msg['title'];
		    }
			singleVideo.resumeTime = time;
			var videoList = new Playlist();
			videoList.push(singleVideo);
			var myPlayer = new Player();			
			myPlayer.playlist = videoList;
			//var overlayDocument = createSubtitleDocument();
			//var subtitle = overlayDocument.getElementsByTagName("text").item(0);
			myPlayer.play();
			var currenttime = 0;
			var duration;
			console.log("media item duration: "+myPlayer.currentMediaItemDuration);
			if (myPlayer.currentMediaItemDuration == null) { //pre tvos 10
				duration = 0;
				myPlayer.addEventListener("shouldHandleStateChange", function(e) {
					duration = e.duration;
				});
			}
			myPlayer.addEventListener("timeDidChange", function(info) {
				currenttime = info.time;				
				//hack for duration
				if (duration == 0) {
					if (myPlayer.currentMediaItemDuration != null && myPlayer.currentMediaItemDuration != 0) {
						duration = myPlayer.currentMediaItemDuration;
					} else {
						myPlayer.pause(); //this will trigger "shouldHandleStateChange"
						setTimeout(function(){
							myPlayer.play();
						},100);
					}
				}
				//subtitle.textContent = "timeDidChange "+info.time;
			}, {"interval":1});			
			myPlayer.addEventListener("stateDidChange", function(e) {  
				if(e.state == "end") {
					options.abort();
					if ((duration - currenttime) * 100/duration <=3) { //if we've stopped at more than 97% play time, don't resume
						currenttime = 0;
					}
					playCache[msg['url']] = currenttime;
					localStorage.setItem('playCache', JSON.stringify(playCache)); //save this url's stop time for future playback
					this.fetch({
						url:msg['stop']+"/"+btoa(currenttime.toString()),
						abort: function() {
							//do nothing
						}
					});
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
		} else if (xhr.status == 210) {
			var msg = JSON.parse(xhr.responseText);
			if (msg['type'] == 'saveSettings') {
				saveSettings(msg['addon'], msg['settings']);
				options.abort();
			} else if(msg['type'] == 'loadSettings') {
				var settings = loadSettings(msg['addon']);
				this.post({
					url:'/response/'+msg['msgid'],
					data:btoa(JSON.stringify(settings))
				});
				setTimeout(function() {
					options.url = msg['url']
					this.fetch(options);
				}.bind(this), 1000)				
			}
		} else if (xhr.status == 212) {
			var msg = JSON.parse(xhr.responseText);
			options.url = msg['url'];
			this.fetch(options);
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
    if (typeof document.getElementById("progress")!="undefined") { //progress dialog
	    var progress = document.getElementById("progress");
	    var url = progress.getAttribute("documentURL");
	    var id = progress.getAttribute("msgid");
	    setTimeout(function() {
		    this.fetch({
				url: url,
				success: function(responseDoc) {
					try {
						console.log("updating progress dialog");
						navigationDocument.replaceDocument(responseDoc, document);
					} catch (err) {
						this.post({
							url: "/response/" + id,
							data: "blah"
						});
					}
				}.bind(this),
				abort: function() {
					try {
						console.log("Removing progress dialog");
						var loadingDocument = createLoadingDocument();
						navigationDocument.replaceDocument(loadingDocument, document);
						new DocumentController(this, url, loadingDocument);
					} catch (err) {
						this.post({
							url: "/response/" + id,
							data: "blah"
						});
					}
				}.bind(this)
			});
		}.bind(this), 1000);	    
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
	   	if(elem.hasAttribute("abort")) {
		   	var url = elem.getAttribute("abort");
		   	document.addEventListener("unload", function() {
				notify(url);  	
		   	});
	   	}
	   	if(elem.hasAttribute("abortfunction")) {
		   	//var url = function() { return eval(elem.getAttribute("abortfunction"));}.call({document:document});		   	
		   	document.addEventListener("unload", function() {
			   	eval(elem.getAttribute("abortfunction"));
		   	}.bind(this));
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



