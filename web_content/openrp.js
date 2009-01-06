var origin = null;
var dest = null;

var map = null;
var geocoder;
var busStopIcon;
var walkStopIcon;
var startIcon;
var endIcon;


/**
 * Setup locations based on cookie. Call once during load."
 */
function setupLocations() {
    // if no cookie yet exists, no biggie, these values just won't get set
    // to anything
    document.getElementById('routePlanStart').value = YAHOO.util.Cookie.getSub("routeplan", "start"); 
    document.getElementById('routePlanEnd').value = YAHOO.util.Cookie.getSub("routeplan", "end");         
}

/**
 * Initialize icons. Call once during load.
 */
function initIcons() {
    busStopIcon = new GIcon();
    busStopIcon.image = "lib/small_bus_marker.png";
    busStopIcon.iconSize = new GSize(64, 52);
    busStopIcon.iconAnchor = new GPoint(5, 47);

    walkStopIcon = new GIcon();
    walkStopIcon.image = "lib/small_walk_marker.png";
    walkStopIcon.iconSize = new GSize(30, 50);
    walkStopIcon.iconAnchor = new GPoint(5, 45);    
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

function submitCallback(data, responseCode) {
    planButton = document.getElementById('plan-button');
    planButton.value = 'Plan!';
    planButton.style.color = "#000";

    if (responseCode != 200) {
        return;
    }

    actions = eval(data);

    // update the map, if we have one
    if (map) {
        updateMapDirections(actions);
    }

    // now update our directions
    var routePlan = "";

    if (actions.length == 0) {
        routePlan += "We couldn't find any transit directions for this trip. ";
        routePlan += "This probably means it's faster to walk.";
    } else {
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

        routePlan += "<p><b>" + actions[0].time + ":</b> ";
        routePlan += "Walk to " + first_stop + ".</p>";

        for (var i = 0; i < actions.length; ++i) {

            if (actions[i].type == "board") {                
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Board the " + actions[i].route_shortname + " (";
                routePlan += actions[i].route_longname + ").</p>";
            } else if (actions[i].type == "alight") {
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Descend at " + actions[i].stopname;

                if (actions.length > i+1 && actions[i].type == "alight" && 
                    actions[i+1].type != "board") {
                    routePlan += " and walk to " + dest_str;
                }
                routePlan += ".</p>";
            } 
            
            if (i==(actions.length-1)) {
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Arrive at " + dest_str + ".</p>";
            }
        }
    }

    document.getElementById("route-plan-content").innerHTML = routePlan;

    // show the route plan, hide the about box
    document.getElementById('route-plan').style.display = 'block';
    document.getElementById('intro').style.display = 'none';

    //showDebugInfo(actions);
}

function updateMapDirections(actions) {
    // nuke any existing map overlays
    map.clearOverlays();
    
    // add start and end markers
    function orderOfCreation(marker,b) {
        return 1;
    }

    map.addOverlay(new GMarker(origin, {icon:G_START_ICON}));
    map.addOverlay(new GMarker(dest, {icon:G_END_ICON}));

    var routePath = new Array();

    var walkPathColour = "#0000ff";
    var busPathColour = "#ff0000";

    var bounds = new GLatLngBounds;
    bounds.extend(origin);
    bounds.extend(dest);

    if (actions.length == 0) {
        addWalkingOverlay(origin, dest);
    } else {
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
                markerOpts.labelOffset = new GSize(24, -44);
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
    }
    map.setCenter(bounds.getCenter());
    var zoom = map.getBoundsZoomLevel(bounds);
    map.setCenter(bounds.getCenter(), zoom);

    addLine(map, routePath, walkPathColour);
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
        YAHOO.util.Cookie.setSubs("routeplan", 
                                  { start: document.getElementById('routePlanStart').value, 
                                      end: document.getElementById('routePlanEnd').value },
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
        document.getElementById('routePlanStart').style.border = 
        '1px solid #aaf';
    } else {
        document.getElementById('error-from').style.display = 'block';
        document.getElementById('routePlanStart').style.border = 
        '2px solid #f00';
    }

    checkPlanRoute();
}

function gotDestCallback(latlng) {
    if (latlng) {
        dest = latlng;
        document.getElementById('error-to').style.display = 'none';
        document.getElementById('routePlanEnd').style.border = 
        '1px solid #aaf';
    } else {
        document.getElementById('error-to').style.display = 'block';
        document.getElementById('routePlanEnd').style.border = 
        '2px solid #f00';
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
