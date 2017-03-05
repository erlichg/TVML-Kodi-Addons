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
DocumentLoader.prototype.fetchPost = function(options) {
    if (typeof options.url !== "string") {
        throw new TypeError("DocumentLoader.fetch: url option must be a string.");
    }
    if (typeof options.data == "undefined" || options.data == "") {
        options.type = "GET";
    } else {
        options.type = "POST";
    }
    //display loading document
    if (typeof options.silent == "undefined" || !options.silent) {
        addLoadingDocument();
    }

    // Parse the request URL
    const docURL = this.prepareURL(options.url);
    const xhr = new XMLHttpRequest();
    xhr.open(options.type, docURL);
    xhr.responseType = "json";
    xhr.onload = function() {
        try {
            var msg = xhr.response;
            console.log('Got message type='+msg['messagetype']+' and end='+msg['end']);
            var end = msg['end'];
            var type = msg['messagetype'] || "undefined";
            if (typeof options.onload == "function") {
                options.onload(msg);
            }
            if (type == 'play') { //play
                var time = msg['time'];
                //VLC player
                try {
                    if (time != 0) {
                        var formattedTime = this.formatTime(Math.floor(time/1000)); //convert to fomatted time in seconds
                        if (formattedTime == "00:00") {
                            this.play(msg, 0, function(time) {
                                //continue if needed
                                if (typeof end == "undefined" || !end) {
                                    options.url = msg['return_url'];
                                    this.fetchPost(options);
                                }
                            }.bind(this));
                        } else {
                            var resume = createResumeDocument(formattedTime);
                            resume.getElementById("resume").addEventListener("select", function() {
                                navigationDocument.removeDocument(resume);
                                this.play(msg, time, function(time) {
                                    //continue if needed
                                    if (typeof end == "undefined" || !end) {
                                        options.url = msg['return_url'];
                                        this.fetchPost(options);
                                    }
                                }.bind(this));
                            }.bind(this));
                            resume.getElementById("begin").addEventListener("select", function() {
                                navigationDocument.removeDocument(resume);
                                this.play(msg, 0, function(time) {
                                    //continue if needed
                                    if (typeof end == "undefined" || !end) {
                                        options.url = msg['return_url'];
                                        this.fetchPost(options);
                                    }
                                }.bind(this));
                            }.bind(this));
                            replaceLoadingDocument(resume);
                        }
                    } else {
                        this.play(msg, time, function(time) {
                            //continue if needed
                            if (typeof end == "undefined" || !end) {
                                options.url = msg['return_url'];
                                this.fetchPost(options);
                            }
                        }.bind(this));
                    }
                } catch (e) {
                    console.log(e);
                    //continue if needed
                    if (typeof end == "undefined" || !end) {
                        options.url = msg['return_url'];
                        this.fetchPost(options);
                    }
                }

            } else if(type == 'nothing') { //do nothing
                //no message
                if (typeof end == "undefined" || !end) {
                    options.url = msg['return_url'];
                    this.fetchPost(options);
                } else {
                	removeLoadingDocument();
				}
            } else if(type == 'modal') { //modal results
                var responseDoc = new DOMParser().parseFromString(msg['doc'], "application/xml");
                responseDoc = this.prepareDocument(responseDoc);
                options.success(responseDoc, true);
                if (typeof end == "undefined" || !end) {
                    options.url = msg['return_url'];
                    options.silent = true; //load next page silently so as not to show loading document
                    this.fetchPost(options);
                }
            } else if (type == 'load') { //load url
                var url = msg['url'];
                var data = null;
                if (typeof msg['data'] != "undefined") {
                    data = msg['data'];
                }
                var initial = false;
                if (typeof msg['initial'] != "undefined") {
                    initial = msg['initial']
                }
                if (typeof msg['replace'] == 'boolean' && msg['replace'] && navigationDocument.documents.length > 1) {
                    navigationDocument.popDocument(); //remove top most document
                }
                setTimeout(function() {
                    var match = /\/catalog\/(.*)/.exec(url);
                    if (match != null) {
                        catalog(match[1], data);
                    } else {
                        new DocumentController(this, url, initial, data);
                    }
                }.bind(this), 500);
            } else if (type == 'progress') { //new progress
                if (typeof this.progressDocument == "undefined") {
                    this.progressDocument = new DOMParser().parseFromString(msg['doc'], "application/xml"); //save progress
                    this.progressDocument.addEventListener("unload", function() { //in case of user cancel, send abort notification
                        if (typeof this.progressDocument != "undefined") {
                            this.progressDocument = undefined;
                            if (typeof msg['stop'] != "undefined") { //only if response is required
                                notify(msg['stop'])
                            }
                        }
                    }.bind(this));
                    var progress = this.progressDocument.getElementById("progress")
                    var url = progress.getAttribute("documentURL");
                    var id = progress.getAttribute("msgid");
                    //display progress document
                    if (typeof options.success === "function") {
                        options.success(this.progressDocument);
                    } else {
                        replaceLoadingDocument(this.progressDocument);
                    }
                }
                var progress = this.progressDocument.getElementById("progress")
                var url = progress.getAttribute("documentURL");
                var data = progress.getAttribute("data");
                //fetch new message
                options.url = url;
                options.silent = true;
                options.data = data;
                options.onload = function(msg) {
                    var type = msg['messagetype'];
                    if (type == 'progress' || type == 'updateprogress' || type == 'closeprogress') {
                        //do nothing. Let builting handlers deal with this
                    } else if (typeof this.progressDocument != "undefined" && navigationDocument.documents.indexOf(this.progressDocument) != -1) { //we got other type of document and progress is still showing so we need to remove it
                        console.log('Manually removing progress document');
                        const temp = this.progressDocument; //save it
                        this.progressDocument = undefined; //delete it so as not to call "unload"
                        navigationDocument.removeDocument(temp);
                    }
                }.bind(this)
                this.fetchPost(options);
            } else if (type == 'updateprogress') { //update progress
                if (typeof this.progressDocument != "undefined") {
                    var progress = this.progressDocument.getElementById("progress");
                    var url = progress.getAttribute("documentURL");
                    var id = progress.getAttribute("msgid");
                    var data = progress.getAttribute("data");
                    //update progress document with updated values
                    try {
                        console.log("updating progress dialog");
                        var new_doc = new DOMParser().parseFromString(msg['doc'], "application/xml");
                        var updated_progress = new_doc.getElementById("progress");
                        progress.setAttribute('value', updated_progress.getAttribute('value'))
                        var updated_text = new_doc.getElementById("text");
                        this.progressDocument.getElementById("text").textContent = updated_text.textContent;
                    } catch (err) {
                        console.log("Failed to update progress dialog");
                    }
                } else {
                    var progress = new DOMParser().parseFromString(msg['doc'], "application/xml").getElementById('progress');
                    var url = progress.getAttribute("documentURL");
                    var id = progress.getAttribute("msgid");
                    var data = progress.getAttribute("data");
                }
                //fetch new message
                options.url = url;
                options.silent = true;
                options.data = data;
                options.onload = function(msg) {
                    var type = msg['messagetype'];
                    if (type == 'progress' || type == 'updateprogress' || type == 'closeprogress') {
                        //do nothing. Let builting handlers deal with this
                    } else if (typeof this.progressDocument != "undefined" && navigationDocument.documents.indexOf(this.progressDocument) != -1) { //we got other type of document and progress is still showing so we need to remove it
                        console.log('Manually removing progress document');
                        const temp = this.progressDocument; //save it
                        this.progressDocument = undefined; //delete it so as not to call "unload"
                        navigationDocument.removeDocument(temp);
                    }
                }.bind(this)
                this.fetchPost(options);
            } else if (type == 'closeprogress') {
                if (typeof this.progressDocument != "undefined") {
                	setTimeout(function() {
                		console.log("Removing progress dialog");
                    	var save = this.progressDocument;
                    	this.progressDocument = undefined;
                    	navigationDocument.removeDocument(save);
					}.bind(this), 500);

                }
                if (typeof end == "undefined" || !end) {
                    options.url = msg['return_url'];
                    options.silent = false;
                    this.fetchPost(options);
                }
            } else if (type == 'special') { //special results
                if (typeof options.special == "function") {
                    options.special(msg['ans']);
                }
                if (typeof end == "undefined" || !end) {
                    options.url = msg['return_url'];
                    this.fetchPost(options);
                }
            } else if (type == 'refresh') { //refresh current doc
				if (navigationDocument.documents.indexOf(singleton_loading_document) != -1) {
                    var doc_to_refresh = navigationDocument.documents[navigationDocument.documents.length - 2];
                } else {
					var doc_to_refresh = navigationDocument.documents[navigationDocument.documents.length - 1];
				}
				var url = doc_to_refresh.documentElement.getAttribute('data-url');
				url = url.substring(0, url.lastIndexOf('/')); //remove the process part since we want a fresh call
				var data = doc_to_refresh.documentElement.getAttribute('data-item-url');
				new DocumentController(documentLoader, url, false, data, true);
            } else { //regular document
                responseDoc = new DOMParser().parseFromString(msg['doc'], "application/xml");
                responseDoc = this.prepareDocument(responseDoc);
                responseDoc.documentElement.setAttribute('data-item-url', msg['item_url']);
                responseDoc.documentElement.setAttribute('data-url', msg['return_url']);
                if (typeof options.initial == "boolean" && options.initial) {
                    console.log("registering event handlers");
                    responseDoc.addEventListener("disappear", function () {
                        if (navigationDocument.documents.length == 1) {
                            //if we got here than we've exited from the web server since the only page (root) has disappeared
                            App.onExit({});
                        }
                    }.bind(this));
                    setTimeout(function () {
                        if (typeof options.success === "function") {
                            options.success(responseDoc);
                        } else {
                            replaceLoadingDocument(responseDoc);
                        }
                    }, 1000);
                } else {
                    if (typeof options.success === "function") {
                        options.success(responseDoc);
                    } else {
                        replaceLoadingDocument(responseDoc);
                    }
                }
                if (typeof end == "undefined" || !end) {
                	responseDoc.addEventListener("unload", function() {
                		options.url = msg['return_url'];
                    	this.fetchPost(options);
					}.bind(this));

                }
            }
        } catch (err) {
			removeLoadingDocument();
            console.log(err);
            if (typeof options.error === "function") {
                options.error(xhr);
            } else {
                const alertDocument = createAlertDocument('Error', 'Failed to load the page');
                navigationDocument.presentModal(alertDocument);
            }
        }
    }.bind(this);
    xhr.onerror = function() {
        if (typeof options.onload === "function") {
            options.onload({'messagetype': 'error', 'end': true});
        }
        if (typeof options.error === "function") {
            options.error(xhr);
        } else {
            const alertDocument = createLoadErrorAlertDocument(docURL, xhr, true);
            navigationDocument.presentModal(alertDocument);
            removeLoadingDocument();
        }
    };
    xhr.ontimeout = function() {
        if (typeof options.onload === "function") {
            options.onload({'messagetype': 'timeout', 'end': true});
        }
        if (typeof options.error === "function") {
            options.error(xhr);
        } else {
            const alertDocument = createAlertDocument('Timeout', 'The request timed-out');
            navigationDocument.presentModal(alertDocument);
            removeLoadingDocument();
        }
    }
    xhr.timeout = 3600000; //timeout of 1 hour
    if (typeof options.data == "undefined" || options.data == "") {
        xhr.send();
    } else {
        xhr.send(options.data);
    }
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
    if (url == null) {
        return null;
    }
    if (url.indexOf("/") === 0) {
        url = this.baseURL + url.substr(1);
    }
    return url;
};

/*
 * Helper method to mangle relative URLs in XMLHttpRequest response documents
 */
DocumentLoader.prototype.prepareDocument = function(document) {
    const templates = {};
    var i;
    for (i=0; i<document.documentElement.children.length;i++) {
        if (document.documentElement.children.item(i).tagName.indexOf("Template")!=-1) {
            templates[document.documentElement.children.item(i).getAttribute("id")] = document.documentElement.children.item(i);
        }
    }
    traverseElements(document.documentElement, this.prepareElement);
    if (Object.keys(templates).length == 1 && document.getElementsByTagName("searchTemplate").length == 1) {
        return prepareSearchDocument(document);
    }
    if (typeof document.getElementById("player")!="undefined") { //player
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
                this.fetchPost({
                    url:msg['stop']+"/"+btoa(currenttime.toString()),
                    abort: function() {
                        //do nothing
                    }
                });
            }
        }.bind(this), false);
    }

    if (Object.keys(templates).length > 1) {
        const type = document.getElementsByTagName("head").item(0).getAttribute("id");
        if (type == "segmentBar") {
            const items = {};
            const segmentBar = document.createElement("segmentBarHeader");
            segmentBar.setAttribute("autoHighlight", "true");
            segmentBar.appendChild(document.createElement("segmentBar"));
            segmentBar.firstChild.setAttribute("autoHighlight", "true");

            for (key in templates) {
                var item = document.createElement("segmentBarItem");
                item.setAttribute("class", key);
                item.appendChild(document.createElement("title"));
                item.firstChild.textContent = templates[key].getAttribute("title");
                segmentBar.firstChild.appendChild(item);
                items[key] = item;
            }


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
        } else if (type == "menuBar") {
            const menuBarTemplate = new DOMParser().parseFromString("<document><menuBarTemplate></menuBarTemplate></document>", "application/xml");
            const menuBar = menuBarTemplate.createElement("menuBar");
            const menuBarFeature = menuBar.getFeature("MenuBarDocument");
            //strip document from all templates
            for (key in templates) {
                if (templates[key].parentNode == document.documentElement) {
                    document.documentElement.removeChild(templates[key]);
                }
            }

            for (key in templates) {
                var item = menuBarTemplate.createElement("menuItem");
                item.appendChild(menuBarTemplate.createElement("title"));
                item.firstChild.textContent = templates[key].getAttribute("title");
                menuBar.appendChild(item);
                var doc = new DOMParser().parseFromString("<document>"+document.documentElement.innerHTML+templates[key].outerHTML+"</document>", "application/xml")
                doc = this.prepareDocument(doc);
                menuBarFeature.setDocument(doc, item);
            }
            menuBarTemplate.documentElement.firstChild.appendChild(menuBar);
            return menuBarTemplate;
        }
    }
    traverseElements(document.documentElement, function(elem) {
        if (elem.hasAttribute("notify")) {
            var url = elem.getAttribute("notify");
            elem.addEventListener("select", function() {
                this.fetchPost({
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
        if(elem.hasAttribute("loadfunction")) {
            //var url = function() { return eval(elem.getAttribute("loadfunction"));}.call({document:document});
            document.addEventListener("load", function() {
                eval(elem.getAttribute("loadfunction"));
            }.bind(this));
        }
    }.bind(this));
    return document;
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

DocumentLoader.prototype.play = function(msg, time, callback) {
    try {
    	var currenttime = 0;
		var duration = 0;
        var player = VLCPlayer.createPlayerWithUrlTimeImageDescriptionTitleImdbSeasonEpisodeCallback(msg['url'], time, this.prepareURL(msg['image']), msg['description'], msg['title'], msg['imdb'], msg['season'], msg['episode'], function(time) {
            try {
                duration = player.getDuration();
                currenttime = time;
                console.log("player ended with "+currenttime+"ms out of "+duration+"ms");
                if (typeof currenttime == "undefined") {
                    currenttime == 0;
                }
                if (typeof duration == "undefined") {
                	duration = 0;
                }
				var url = this.prepareURL(msg['stop'] + "/" + btoa(JSON.stringify({'time': currenttime.toString(), 'total': duration.toString()})));
				console.log("notifying " + url);
				VLCPlayer.notify(url);
            } catch (e) {
                console.log(e);
            }
            setTimeout(function() {
				callback(currenttime);
			}, 0);
        }.bind(this));
        console.log("after create player: "+player);

        if (typeof(player) == "string") { //an error has occured
            throw player;
        } else if (typeof(player) != "undefined") {
            VLCPlayer.present(player);
        } else {
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
            //singleVideo.resumeTime = time / 1000; //convert to seconds
            var videoList = new Playlist();
            videoList.push(singleVideo);

            var myPlayer = new Player();
            console.log("old player");
            myPlayer.playlist = videoList;
            myPlayer.play();
            myPlayer.seekToTime(time);



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
            }, {"interval":1});
            myPlayer.addEventListener("stateDidChange", function(e) {
                if(e.state == "end") {
                	try {
                        currenttime = currenttime * 1000; //since we're getting ms from player
						var url = this.prepareURL(msg['stop'] + "/" + btoa(JSON.stringify({'time': currenttime.toString(), 'total': duration.toString()})));
						notify(url);
                    } catch (err) {
                		console.log(err);
					}
                    setTimeout(function() {
						callback(currenttime);
					});
                }
            }.bind(this), false);
        }
        removeLoadingDocument();
        if (typeof duration == "undefined") {
        	duration = 0;
		}
        setTimeout(function() {
        	var url = this.prepareURL(msg['start'] + "/" + btoa(duration.toString()));
			notify(url);
		}.bind(this), 0);
    } catch (e) {
    	removeLoadingDocument();
        console.log(e);
        var alert = createAlertDocument("Error", "Error playing URL "+msg['url'], true);
        navigationDocument.presentModal(alert);
        setTimeout(function() {
			callback(null);
		});

    }

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
    return ("0" + hours).slice(-2)+":"+this.formatTime(time%3600);
}

