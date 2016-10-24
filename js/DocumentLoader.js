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
    xhr.timeout = 30000;
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
		    
		    //VLC player
		    try {
			    if (time != 0) {
				    var formattedTime = this.formatTime(Math.floor(time/1000)); //convert to fomatted time in seconds
				    if (formattedTime == "00:00") {
					    this.play(msg, 0, playCache, options);
				    } else {
				    	var resume = createResumeDocument(formattedTime);
				    	resume.getElementById("resume").addEventListener("select", function() {
						    navigationDocument.removeDocument(resume);
						    this.play(msg, time, playCache, options);
				    	}.bind(this));
				    	resume.getElementById("begin").addEventListener("select", function() {
						    navigationDocument.removeDocument(resume);
						    this.play(msg, 0, playCache, options);
				    	}.bind(this));
				    	navigationDocument.pushDocument(resume);
				    }
			    } else {
				    this.play(msg, time, playCache, options);
			    }
			    
			    return;
		    } catch (e) {
			    console.log(e);
		    }
			
			
			
		    //Built-in player
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
/*
			try {
				var playerDocument = createPlayerDocument(msg['image']);
				playerDocument.addEventListener("load", function() {
					var myPlayer = playerDocument.getElementsByTagName("mediaContent").item(0).getFeature("Player");
					myPlayer.playlist = videoList;
					console.log("presented new player");
				});
				
				navigationDocument.pushDocument(playerDocument);				
				//myPlayer.present();				
			} catch (err) {
*/
				var myPlayer = new Player();
				console.log("old player");
				myPlayer.playlist = videoList;
				myPlayer.play();
// 			}
						
			
			//var overlayDocument = createSubtitleDocument();
			//myPlayer.overlay = overlayDocument;
			//var subtitle = overlayDocument.getElementsByTagName("text").item(0);
			options.abort(); //remove the loading document
						
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
    xhr.timeout = 30000;
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
	    if (typeof this.progressDocument == "undefined") {
		    this.progressDocument = document; //save progress
	    }	    
	    var progress = this.progressDocument.getElementById("progress")
	    var url = progress.getAttribute("documentURL");
	    var id = progress.getAttribute("msgid");
	    //setTimeout(function() {
		    this.fetch({
				url: url,
				success: function(responseDoc) {
					try {
						console.log("updating progress dialog");
						var updated_progress = responseDoc.getElementById("progress");
						progress.setAttribute('value', updated_progress.getAttribute('value'))
						var updated_text = responseDoc.getElementById("text");
						this.progressDocument.getElementById("text").textContent = updated_text.textContent;
						//navigationDocument.replaceDocument(responseDoc, document);
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
						this.post({
							url: "/response/" + id,
							data: "blah"
						});						
						var loadingDocument = createLoadingDocument();
						navigationDocument.replaceDocument(loadingDocument, this.progressDocument);
						delete this.progressDocument;						
						new DocumentController(this, url, loadingDocument);
					} catch (err) {
					}					
					
				}.bind(this)
			});
		//}.bind(this), 1000);	    
    } else if (typeof document.getElementById("player")!="undefined") { //player
	    console.log("in new player");
	    var m = document.getElementById("player");
	    var singleVideo = new MediaItem(m.getAttribute('type'), m.getAttribute('url'));
		var videoList = new Playlist();
		videoList.push(singleVideo);
		var myPlayer = m.getFeature('Player');
		console.log("found player "+myPlayer);		
		myPlayer.playlist = videoList;
		//var subtitle = m.getElementsByTagName("text").item(0);
		myPlayer.present();
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
    } else if (document.getElementsByTagName("placeholder").length != 0) {
		var i;
		const templates = {};
		for (i=0; i<document.documentElement.children.length;i++) {
			if (document.documentElement.children.item(i).tagName.indexOf("Template")!=-1) {			
				templates[document.documentElement.children.item(i).getAttribute("id")] = document.documentElement.children.item(i);
			}
		}
		const items = {};
		const segmentBar = document.createElement("segmentBarHeader");
		segmentBar.setAttribute("autoHighlight", "true");
		segmentBar.appendChild(document.createElement("segmentBar"));
		segmentBar.firstChild.setAttribute("autoHighlight", "true");
		var item = document.createElement("segmentBarItem");
		item.setAttribute("class", "list");
		item.appendChild(document.createElement("title"));
		item.firstChild.textContent = "Details";
		segmentBar.firstChild.appendChild(item);
		items["list"] = item;
		
		item = document.createElement("segmentBarItem");
		item.setAttribute("class", "nakedlist");
		item.appendChild(document.createElement("title"));
		item.firstChild.textContent = "List";
		segmentBar.firstChild.appendChild(item);
		items["nakedlist"] = item;
		
		item = document.createElement("segmentBarItem");
		item.setAttribute("class", "grid");
		item.appendChild(document.createElement("title"));
		item.firstChild.textContent = "Grid";
		segmentBar.firstChild.appendChild(item);
		items["grid"] = item;
		
		segmentBar.firstChild.addEventListener('highlight', function(event) {
            selectItem(event.target);
        }); 
		var selectItem = function(selectedElem) {			
		    const cls = selectedElem.getAttribute("class");
		    for (key in templates) {
			    if (templates[key].parentNode == document.documentElement) {
			    	document.documentElement.removeChild(templates[key]);
			    }
		    }
		    var placeholder = templates[cls].getElementsByTagName("placeholder").item(0);
		    for (item in items) {
			    items[item].removeAttribute("autoHighlight");
		    }
		    items[cls].setAttribute("autoHighlight", "true");
		    placeholder.parentNode.insertBefore(segmentBar, placeholder);
		    document.documentElement.appendChild(templates[cls]);	    
		}
		
		selectItem(segmentBar.firstChild.firstChild);		   			                		
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

DocumentLoader.prototype.play = function(msg, time, playCache, options) {
	var player = VLCPlayer.createPlayerWithUrlTimeImageDescriptionTitleImdbSeasonEpisodeCallback(msg['url'], time, msg['image'], msg['description'], msg['title'], msg['imdb'], msg['season'], msg['episode'], function(time) {
		try {
			var total = player.getDuration();
			console.log("player ended with "+time+"ms out of "+total+"ms");
			if ((total - time) * 100/total <=3) { //if we've stopped at more than 97% play time, don't resume
				time = 0;
			}
			console.log("calculated time is "+time);
			playCache[msg['url']] = time;
			localStorage.setItem('playCache', JSON.stringify(playCache)); //save this url's stop time for future playback
			var url = this.prepareURL(msg['stop']+"/"+btoa(time.toString()));
			console.log("notifying "+url);
			VLCPlayer.notify(url);
		} catch (e) {
			console.log(e);
		}
	}.bind(this));
	console.log("after create player: "+player);
	VLCPlayer.present(player);
	options.abort(); //remove the loading document
}

DocumentLoader.prototype.formatTime = function(time) {
	if (time < 60) { //less than a minute
		var seconds = Number(time).toFixed(0);
		return "00:"+("0" + seconds).slice(-2);
	}
	if (time < 3600) { //less than an hour
		var minutes = Math.floor(time / 60);
		var seconds = time%60;
		return ("0" + minutes).slice(-2)+":"+("0" + seconds).slice(-2);
	}
	var hours = Math.floor(time / 3600);
	return ("0" + hours).slice(-2)+":"+formatTime(time%3600);
}

