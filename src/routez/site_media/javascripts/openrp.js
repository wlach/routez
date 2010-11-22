var routePlan;
var map = null;
var bb = null;

var busStopIcon;
var walkStopIcon;
var startIcon;
var endIcon;

/**
 * Setup locations based on previous browser locations or cookie. Call 
 * during or after location changes. Returns true if we should try to load
 * a path, false otherwise.
 */
function setupRoutePlanForm(state) {
    // first, set defaults

    // if no cookie yet exists, no biggie, these values just won't get set
    // to anything
    // FIXME: Actually no, you see null on internet explorer. must fix.    
    var routePlanStartDefault = YAHOO.util.Cookie.getSub("routeplan", "start");
    var routePlanEndDefault = YAHOO.util.Cookie.getSub("routeplan", "end");

    // setup focus handling
    $('input#routePlanStart').focus(function() {
	if (this.value === routePlanStartDefault) {
	    this.select();
	}
    });
    $('input#routePlanStart').mouseup(function(e) { e.preventDefault(); });

    $('input#routePlanEnd').focus(function() {
	if (this.value === routePlanEndDefault) {
	    this.select();
	} 
	return false;
    });
    $('input#routePlanEnd').mouseup(function(e) { e.preventDefault(); });

    $('input#routePlanTime').focus(function() { this.select(); });
    $('input#routePlanTime').mouseup(function(e) { e.preventDefault(); });
    
    if (state === "default") {        
        // if no history state, then (try) to load locations from cookies
        $('input#routePlanStart').val(routePlanStartDefault);
        $('input#routePlanEnd').val(routePlanEndDefault);

        return false;
    } 

    // otherwise we try to get history out of json 
    // FIXME: no error handling here yet
    var stateHash = YAHOO.lang.JSON.parse(state);
    $('input#routePlanStart').val(stateHash.saddr);
    $('input#routePlanEnd').val(stateHash.daddr);
    $('input#routePlanTime').val(stateHash.time);
    
    return true;
}

function reverseDirections() {
    var tmp = $('#routePlanStart').val()
    $('#routePlanStart').val($('#routePlanEnd').val());
    $('#routePlanEnd').val(tmp);
}

// Capitalizes a string, first letter in upper case and the rest in lower case.
// Created: 2005.11.20  - Modified 2005.11.21
//+ Jonas Raoni Soares Silva
//@ http://jsfromhell.com/string/capitalize [rev. #1]
String.prototype.capitalize = function(){
    return this.replace(/\w+/g, function(a){
        return a.charAt(0).toUpperCase() + a.slice(1).toLowerCase();
    });
};

// Strip leading and trailing white-space
// @http://bytes.com/groups/javascript/165013-how-javascript-trim-normalize-space-functions
String.prototype.trim = function() {
    return this.replace(/^\s*|\s*$/g, "");
}

// Replace repeated spaces, newlines and tabs with a single space
// @http://bytes.com/groups/javascript/165013-how-javascript-trim-normalize-space-functions
String.prototype.normalize_space = function() {
    return this.replace(/^\s*|\s(?=\s)|\s*$/g, "");
}

function initMap(cmKey, cmStyleId, minLat, minLon, maxLat, maxLon) {
    // initialize map
    var cloudmade = new CM.Tiles.CloudMade.Web({key: cmKey, styleId: cmStyleId });
    bb = new CM.LatLngBounds(new CM.LatLng(minLat, minLon),new CM.LatLng(maxLat, maxLon));
    map = new CM.Map('map', cloudmade);
    map.addControl(new CM.LargeMapControl());
    map.enableScrollWheelZoom();
    map.enableDoubleClickZoom();
    map.enableShiftDragZoom();

    /*
    walkStopIcon = new CM.Icon();
    walkStopIcon.image = "site_media/images/marker_walk.png";
    walkStopIcon.iconSize = new GSize(46, 36);
    walkStopIcon.iconAnchor = new GPoint(1, 35);

    ferryStopIcon = new CM.Icon();
    ferryStopIcon.image = "site_media/images/marker_ferry.png";
    ferryStopIcon.iconSize = new GSize(46, 36);
    ferryStopIcon.iconAnchor = new GPoint(1, 35);

    switchStopIcon = new CM.Icon();
    switchStopIcon.image = "site_media/images/marker_switch.png";
    switchStopIcon.iconSize = new GSize(46, 36);
    switchStopIcon.iconAnchor = new GPoint(1, 35);
    */
    startIcon = new CM.Icon();
    startIcon.image = "site_media/images/marker_from.png";
    startIcon.iconSize = new CM.Size(34, 36);
    startIcon.iconAnchor = new CM.Point(11, 35);
    
    endIcon = new CM.Icon();
    endIcon.image = "site_media/images/marker_to.png";
    endIcon.iconSize = new CM.Size(34, 36);
    endIcon.iconAnchor = new CM.Point(11, 35);
}

function reset() {
    // reset everything, called on first load (if no trip) and in case
    // of error
    $('#route-plan').hide();
    map.setCenter(bb.getCenter(), map.getBoundsZoomLevel(bb)+1);
    map.clearOverlays();
}

function resetPlanButton() {
    $('#plan-button').val('Plan!');
    $('#plan-button').css('color', "#000");
}

function loadRoutePlanForm() {
    $('form#routeplan-form').submit(function() {
	submitRoutePlan();
	return false;
    });
}

function updateMapBounds(actions) {

    var bound_latlngs = new Array();

    for (var i = 0; i < actions.length; ++i) {
        // only alight and pass actions have latlng info
        if (actions[i].type == "alight" || actions[i].type == "pass") {
            bound_latlngs[bound_latlngs.length] = new CM.LatLng(actions[i].lat, actions[i].lng);
        }
    }

    var bounds = new CM.LatLngBounds(bound_latlngs);
    var zoom = map.getBoundsZoomLevel(bounds);

    map.setCenter(bounds.getCenter(), zoom);
}

function updateMapDirections(start, end, actions) {
    
    // add start and end markers
    function orderOfCreation(marker,b) {
        return 1;
    }

    var routePath = new Array();
    var walkPathColour = "#004";
    var busPathColour = "#22f";

    function addLine(colour) {
	if (routePath.length > 0) {
            var polyline = new CM.Polyline(routePath, colour, 5);
            map.addOverlay(polyline);
	}
    }

    // before doing anything else, set bounds (if we're loading
    // directions on a new page, we need to do this before adding overlays)
    updateMapBounds(actions);

    // nuke any existing map overlays
    map.clearOverlays();

    map.addOverlay(new CM.Marker(new CM.LatLng(start.lat, start.lng), 
                                 { icon: startIcon, title: "start" }));
    map.addOverlay(new CM.Marker(new CM.LatLng(end.lat, end.lng), 
                                 { icon: endIcon, title: "end" }));
    routePath[routePath.length] = new CM.LatLng(start.lat, start.lng);

    for (var i = 0; i < actions.length; ++i) {
        var latlng = new CM.LatLng(actions[i].lat, actions[i].lng);

        if (actions[i].type == "alight" || actions[i].type == "pass") {
            // also add any shape to the path
            if (actions[i].shape) {
                for (var j=0; j<actions[i].shape.length; ++j) {
                    routePath[routePath.length] = new CM.LatLng(
                        actions[i].shape[j][0], actions[i].shape[j][1]);
                }
            } else {
                routePath[routePath.length] = latlng;
            }
        }

        if (actions[i].type == "board") {
            routePath[routePath.length] = latlng;

            if (actions[i].route_type == 3 || actions[i].route_type == 4) {
                var icon = new CM.Icon();
                if (actions[i].route_type == 3)
                    base_name = "site_media/images/generated/marker_bus";
                else
                    base_name = "site_media/images/generated/marker_ferry";
                icon.image =  base_name + actions[i].route_shortname + ".png"
                icon.iconSize = new CM.Size(76, 36);
                icon.iconAnchor = new CM.Point(1, 35);
                map.addOverlay(new CM.Marker(latlng, 
                                             { icon: icon, title: "Board" }));
            } 

            addLine(walkPathColour);
            routePath = new Array();
            routePath[routePath.length] = latlng;
        } else if (actions[i].type == "alight") {
            addLine(busPathColour);
            routePath = new Array();
        } 
            
        // if we have to get off and walk, show a nice icon
        if (i>0 && actions[i-1].type == "alight" && 
            actions[i].type != "board") {
            var icon = new CM.Icon();
            icon.image = "site_media/images/marker_walk.png"
            icon.iconSize = new CM.Size(46, 36);
            icon.iconAnchor = new CM.Point(1, 35);
            map.addOverlay(new CM.Marker(latlng, 
                                         { icon: icon, title: "Walk" }));
        }
    }
    
    routePath[routePath.length] = new CM.LatLng(end.lat, end.lng);
    addLine(walkPathColour);
}

function showMapLink(latlngStr) {
    routePlan += " [<a href=\"http://maps.google.com/maps?q=";
    routePlan += latlngStr + "\">Map</a>]";
}

var routePlanCallbackError = function(o) {
    resetPlanButton();
    $('#error-submit').show();
    reset();
}

var routePlanCallback = function(o) {
    resetPlanButton();

    $('#error-submit').hide(); // clear any previous submit error notices

    try { 
        myresponse = YAHOO.lang.JSON.parse(o.responseText);
    } 
    catch (e) { 
        routePlanCallbackError(o); 
    }

    // check for fails
    errors = myresponse['errors'];
    if (errors) {
        for (var i in errors) {
            if (errors[i] == "start_latlng_decode") {
		$('#routePlanStart').toggleClass('text_error');
		$('#error-from').show();
            }
            if (errors[i] == "end_latlng_decode") {
		$('#routePlanEnd').toggleClass('text_error');
		$('#error-to').show();
            }
        }

        reset();
        return;
    }

    YAHOO.util.Cookie.setSubs("routeplan", 
                              { start: $('input#routePlanStart').val(), 
                                  end: $('input#routePlanEnd').val() },
                              { expires: new Date("January 12, 2025") });

    actions = myresponse['actions'];
    routePlan = "";

    if (map) {
        updateMapDirections(myresponse['start'], myresponse['end'], actions);
    }

    if (actions.length == 0) {
        routePlan = "<p>Couldn't find a path!</p>";
    } else {                
        var origin_str = $('#routePlanStart').val().capitalize().trim().normalize_space();
        var dest_str = $('#routePlanEnd').val().capitalize().trim().normalize_space();
        document.title = "Trip from " + origin_str + " to " + dest_str; 
        first_stop = "";
        for (var i = 0; i < actions.length; ++i) {
            if (actions[i].route_id >= 0) {
                firstStop = actions[i].stopname;
                firstStopLatlng = actions[i].lat + "," + actions[i].lng;
                break;
            }
        }
        if (firstStop == "")
            firstStop = dest_str;

        routePlan += "<ol>";
        routePlan += "<li class='depart'>";
        routePlan += "Start at " + origin_str + ".</li>";
        routePlan += "<li class='walk'><strong>" + actions[0].time + ":</strong> ";
        routePlan += "Begin walking to " + firstStop + ".";
        if (!map) {
            showMapLink(firstStopLatlng);
        }
        routePlan += "</li>";

        for (var i = 0; i < actions.length; ++i) {

            if (actions[i].type == "board") {
                routePlan += "<li class='board'><strong>" + actions[i].time + ":</strong> ";
                routePlan += "Board the " + actions[i].route_shortname + " (";
                routePlan += actions[i].route_longname + ").";
            } else if (actions[i].type == "alight") {
                var previd = actions[i-1].dest_id;
                routePlan += "<li class='alight'><strong>" + actions[i].time + ":</strong> ";
                routePlan += "Descend at " + actions[i].stopname;

                if (actions.length > i+1 && actions[i].type == "alight" && 
                    actions[i+1].type != "board") {
                    routePlan += " and walk to " + dest_str;
                }
                routePlan += ".";
                if (!map) {
                    showMapLink(actions[i].lat + "," + actions[i].lng);
                }
                routePlan += "</li>";
            } 
            
            if (i==(actions.length-1)) {
                routePlan += "<li class='arrive'>";
                routePlan += "Arrive at " + dest_str + " at <strong>" + actions[i].time + "</strong>.";
            }
        }

        routePlan += "</ol>";
    }

    // show a warning if there's too much walking time (only on non-mobile
    // version)
    if (map) {
        if (myresponse['walking_time'] > (20 * 60)) {
            $('#longwalk').show();
        } else {
            $('#longwalk').hide();
        }
    }

    // show the route plan (and options), hide the about box
    document.getElementById('route-plan-content').innerHTML = routePlan;
    //document.getElementById('route-plan-options').style.display = 'block';
    $('#route-plan').show();
    $('#intro').hide();
}

function showDebugInfo(actions) {
    var debug_str = "<p>";
    for (var i = 0; i < actions.length; ++i) {
        debug_str += "Action " + i + ":"; 
        debug_str += " id=" + actions[i].id;
        debug_str += "; route_id=" + actions[i].route_id;
        debug_str += "; type=" + actions[i].type;
        debug_str += "; time=" + actions[i].time;
        debug_str += "; lat=" + actions[i].lat;
        debug_str += "; lng=" + actions[i].lng;
        debug_str += "; stopname=" + actions[i].stopname;
        debug_str += "<br/>\n";
    }
    debug_str += "</p>";

    debug_div = document.getElementById("debug");
    if (!debug_div) {
        document.getElementById("footer").innerHTML += "<div id='debug'></div>";
        debug_div = document.getElementById("debug");
    }
    debug_div.innerHTML = debug_str;
}

function submitRoutePlan() {
    // if google analytics defined, send a page tracker view
    if (typeof(pageTracker) != "undefined") {
	pageTracker._trackPageview('/json/routeplan');
    }

    var start = $('input#routePlanStart').val();
    var end = $('input#routePlanEnd').val();
    var ptime = $('input#routePlanTime').val();

    // clear errors
    $('#error-from').hide();
    $('#error-to').hide();
    $('#routePlanStart').removeClass('text_error');
    $('#routePlanEnd').removeClass('text_error');

    // let user know something exciting is about to happen!
    $('#plan-button').val('Working...');
    $('#plan-button').css('color', "#aaa");

    var currentState = YAHOO.util.History.getCurrentState("plan");
    var newState = YAHOO.lang.JSON.stringify({ saddr: start, 
                                               daddr: end,
                                               time: ptime });

    // if currentState is equal to newState, then we've already set the
    // browser history state to the appropriate value: proceed to plan trip
    // otherwise, we want to setup the history before doing anything else
    if (currentState !== newState) {
        YAHOO.util.History.navigate("plan", newState);
    } else {
        
        YAHOO.util.Connect.asyncRequest("GET", "/json/routeplan" + 
                                        "?start=" + escape(start) + "&end=" + escape(end) +
                                        "&time=" + ptime, 
                                        { success:routePlanCallback, failure:routePlanCallbackError }, null);
        
    }
}
