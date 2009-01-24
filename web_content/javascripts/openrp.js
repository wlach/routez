var origin = null;
var dest = null;

var map = null;
var geocoder;
var busStopIcon;
var walkStopIcon;
var startIcon;
var endIcon;

var routePlanStartDefault = null;
var routePlanEndDefault = null;


/**
 * Setup locations based on cookie. Call once during load.
 */
function setupLocations() {
    // if no cookie yet exists, no biggie, these values just won't get set
    // to anything
    routePlanStartDefault = YAHOO.util.Cookie.getSub("routeplan", "start");
    routePlanEndDefault = YAHOO.util.Cookie.getSub("routeplan", "end");

    document.getElementById('routePlanStart').value = routePlanStartDefault;
    document.getElementById('routePlanEnd').value = routePlanEndDefault;
}

/**
 * Initialize icons. Call once during load.
 */
function initIcons() {
    busStopIcon = new GIcon();
    busStopIcon.image = "lib/images/marker_bus.png";
    busStopIcon.iconSize = new GSize(76, 36);
    busStopIcon.iconAnchor = new GPoint(1, 35);

    walkStopIcon = new GIcon();
    walkStopIcon.image = "lib/images/marker_walk.png";
    walkStopIcon.iconSize = new GSize(46, 36);
    walkStopIcon.iconAnchor = new GPoint(1, 35);

    ferryStopIcon = new GIcon();
    ferryStopIcon.image = "lib/images/marker_ferry.png";
    ferryStopIcon.iconSize = new GSize(46, 36);
    ferryStopIcon.iconAnchor = new GPoint(1, 35);

    switchStopIcon = new GIcon();
    switchStopIcon.image = "lib/images/marker_switch.png";
    switchStopIcon.iconSize = new GSize(46, 36);
    switchStopIcon.iconAnchor = new GPoint(1, 35);

    fromIcon = new GIcon();
    fromIcon.image = "lib/images/marker_from.png";
    fromIcon.iconSize = new GSize(46, 36);
    fromIcon.iconAnchor = new GPoint(1, 35);

    toIcon = new GIcon();
    toIcon.image = "lib/images/marker_to.png";
    toIcon.iconSize = new GSize(46, 36);
    toIcon.iconAnchor = new GPoint(1, 35);
}

function addWalkingOverlay(origin, dest) {
    var directions = new GDirections();
    var options;
    var waypoints = new Array();   
    waypoints[0] = origin.lat() + "," + origin.lng();
    waypoints[1] = dest.lat() + "," + dest.lng();
    directions.loadFromWaypoints(waypoints, {getPolyline: true});
    GEvent.addListener(directions, "load", function() {
            map.addOverlay(directions.getPolyline())}); 
}

function reverseDirections() {
    var tmp = document.getElementById('routePlanStart').value; 
    document.getElementById('routePlanStart').value = document.getElementById('routePlanEnd').value;   
    document.getElementById('routePlanEnd').value = tmp;

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

function addLine(map, routePath, colour) {
    if (routePath.length > 0) {
        var polyline = new GPolyline(routePath, colour, 5);
        map.addOverlay(polyline);
    }
}

function updateMapDirections(actions) {
    // nuke any existing map overlays
    map.clearOverlays();
    
    // add start and end markers
    function orderOfCreation(marker,b) {
        return 1;
    }

    var routePath = new Array();

    var walkPathColour = "#0000ff";
    var busPathColour = "#ff0000";

    bounds = new GLatLngBounds;
    bounds.extend(origin);
    bounds.extend(dest);

    map.addOverlay(new GMarker(origin, {icon:G_START_ICON}));
    map.addOverlay(new GMarker(dest, {icon:G_END_ICON}));

    for (var i = 0; i < actions.length; ++i) {
        if (actions[i].type == "alight" || actions[i].type == "pass") {
            var latlng = new GLatLng(actions[i].lat, actions[i].lng);
            routePath[routePath.length] = latlng;
            bounds.extend(latlng);
            
            // also add any shape to the path
            if (actions[i].shape) {
                for (var j=0; j<actions[i].shape.length; ++j) {
                    routePath[routePath.length] = new GLatLng(
                        actions[i].shape[j][0], actions[i].shape[j][1]);
                }
            }
        }

        if (actions[i].type == "board") {
            var markerOpts = new Object();
            markerOpts.icon = busStopIcon;
            markerOpts.labelText = actions[i].route_shortname;
            markerOpts.labelClass = "tooltip";
            markerOpts.labelOffset = new GSize(31, -35);
            map.addOverlay(new LabeledMarker(latlng, markerOpts));
            
            addLine(map, routePath, walkPathColour);
            routePath = new Array();
        } else if (actions[i].type == "alight") {
            addLine(map, routePath, busPathColour);
            routePath = new Array();
        } 
            
        // if we have to get off and walk, show a nice icon
        if (i>0 && actions[i-1].type == "alight" && 
            actions[i].type != "board") {
            map.addOverlay(new GMarker(latlng, walkStopIcon));
        }               
    }

    addLine(map, routePath, walkPathColour);

    map.setCenter(bounds.getCenter());
    var zoom = map.getBoundsZoomLevel(bounds);
    map.setCenter(bounds.getCenter(), zoom);

}

function submitCallback(data, responseCode) {
    planButton = document.getElementById('plan-button');
    planButton.value = 'Plan!';
    planButton.style.color = "#000";

    if (responseCode != 200) {
        return;
    }

    myresponse = eval( "(" + data + ")");
    actions = myresponse['actions'];
    var routePlan = "";
    
    if (map) {
        updateMapDirections(actions);
    }

    if (actions.length == 0) {
        routePlan = "<p>Couldn't find a path!</p>";
    } else {                
        var origin_str = document.getElementById('routePlanStart').value.capitalize();
        var dest_str = document.getElementById('routePlanEnd').value.capitalize();

        var first_stop = "";
        for (var i = 0; i < actions.length; ++i) {
            if (actions[i].route_id) {
                first_stop = actions[i].stopname;
                break;
            }
        }
        if (first_stop == "")
            first_stop = dest_str;

        routePlan += "<ol>";
        routePlan += "<li class='depart'><strong>" + myresponse['departure_time'] + ":</strong> ";
        routePlan += "Start at " + origin_str + ".</li>";
        routePlan += "<li class='walk'><strong>" + actions[0].time + ":</strong> ";
        routePlan += "Walk to " + first_stop + ".</li>";

        for (var i = 0; i < actions.length; ++i) {

            if (actions[i].type == "board") {
                routePlan += "<li class='board'><strong>" + actions[i].time + ":</strong> ";
                routePlan += "Board the " + actions[i].route_shortname + " (";
                routePlan += actions[i].route_longname + ").</li>";
            } else if (actions[i].type == "alight") {
                var previd = actions[i-1].dest_id;
                routePlan += "<li class='alight'><strong>" + actions[i].time + ":</strong> ";
                routePlan += "Descend at " + actions[i].stopname;

                if (actions.length > i+1 && actions[i].type == "alight" && 
                    actions[i+1].type != "board") {
                    routePlan += " and walk to " + dest_str;
                }
                routePlan += ".</li>";
            } 
            
            if (i==(actions.length-1)) {
                routePlan += "<li class='arrive'><strong>" + actions[i].time + ":</strong> ";
                routePlan += "Arrive at " + dest_str + ".</li>";
            }
        }

        routePlan += "</ol>";
    }

    // show the route plan (and options), hide the about box
    document.getElementById('route-plan-content').innerHTML = routePlan;
    document.getElementById('route-plan').style.display = 'block';
    document.getElementById('route-plan-options').style.display = 'block';
    document.getElementById('intro').style.display = 'none';
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

function checkPlanRoute() {
 
    if (origin && dest) {
        routePlanStartDefault = document.getElementById('routePlanStart').value;
        routePlanEndDefault = document.getElementById('routePlanEnd').value;

        YAHOO.util.Cookie.setSubs("routeplan", 
                                  { start: routePlanStartDefault, 
                                      end: routePlanEndDefault },
                                  { expires: new Date("January 12, 2025") });

        time = document.getElementById('time').value;

        url = "/json/routeplan" + 
        "?startlat=" + origin.lat() + "&startlng=" + origin.lng() +
        "&endlat=" + dest.lat() + "&endlng=" + dest.lng() + 
        "&time=" + time;
        GDownloadUrl(url, submitCallback);

        planButton = document.getElementById('plan-button');
        planButton.value = 'Working...';    
        planButton.style.color = "#aaa";
    }
}

function gotOriginCallback(latlng) {
    if (latlng) {
        origin = latlng;
        document.getElementById('error-from').style.display = 'none';
    } else {
        document.getElementById('error-from').style.display = 'block';
        document.getElementById('routePlanStart').style.border = 
        '1px solid #800000';
    }

    checkPlanRoute();
}

function gotDestCallback(latlng) {
    if (latlng) {
        dest = latlng;
        document.getElementById('error-to').style.display = 'none';
    } else {
        document.getElementById('error-to').style.display = 'block';
        document.getElementById('routePlanEnd').style.border = 
        '1px solid #800000';
    }

    checkPlanRoute();
}

function mysubmit() {
    origin = dest = null;
    
    var extra = ", Halifax, Nova Scotia";
    var origin_str = document.getElementById('routePlanStart').value + extra;
    var dest_str = document.getElementById('routePlanEnd').value + extra;
    geocoder.getLatLng(origin_str, gotOriginCallback);
    geocoder.getLatLng(dest_str, gotDestCallback);
}


function locationInputFocused(location) {
    if (location == "start" && 
        document.getElementById('routePlanStart').value == routePlanStartDefault) {
        document.getElementById('routePlanStart').select();
    } else if (location == "end" && document.getElementById('routePlanEnd').value == routePlanEndDefault) {
        document.getElementById('routePlanEnd').select();
    }
}
