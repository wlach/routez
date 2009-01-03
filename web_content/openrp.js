var origin = null;
var dest = null;

var map;
var geocoder;
var busStopIcon;
var walkStopIcon;
var startIcon;
var endIcon;

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

    // show the route plan, hide the about box
    document.getElementById('route-plan').style.display = 'block';
    document.getElementById('intro').style.display = 'none';

    // nuke any existing map overlays
    map.clearOverlays();
    
    // add start and end markers
    function orderOfCreation(marker,b) {
        return 1;
    }

    map.addOverlay(new GMarker(origin, {icon:G_START_ICON}));
    map.addOverlay(new GMarker(dest, {icon:G_END_ICON}));

    actions = eval(data);
    var routePlan = "";
    var routePath = new Array();

    var walkPathColour = "#0000ff";
    var busPathColour = "#ff0000";

    var bounds = new GLatLngBounds;
    bounds.extend(origin);
    bounds.extend(dest);

    if (actions.length == 0) {
        routePlan += "We couldn't find any transit directions for this trip. ";
        routePlan += "This probably means it's faster to walk.";
        addWalkingOverlay(origin, dest);
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
                
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Board the " + actions[i].route_shortname + " (";
                routePlan += actions[i].route_longname + ").</p>";

                addLine(map, routePath, walkPathColour);
                routePath = new Array();
            } else if (actions[i].type == "alight") {
                var previd = actions[i-1].dest_id;
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Descend at " + actions[i].stopname;

                if (actions.length > i+1 && actions[i].type == "alight" && 
                    actions[i+1].type != "board") {
                    routePlan += " and walk to " + dest_str;
                }
                routePlan += ".</p>";

                addLine(map, routePath, busPathColour);
                routePath = new Array();
            } 
            
            // if we have to get off and walk, show a nice icon
            if (i>0 && actions[i-1].type == "alight" && 
                actions[i].type != "board") {
                map.addOverlay(new GMarker(latlng, walkStopIcon));
            }

            if (i==(actions.length-1)) {
                routePlan += "<p><b>" + actions[i].time + ":</b> ";
                routePlan += "Arrive at " + dest_str + ".</p>";
            }
        }
    }
    map.setCenter(bounds.getCenter());
    var zoom = map.getBoundsZoomLevel(bounds);
    map.setCenter(bounds.getCenter(), zoom);

    addLine(map, routePath, walkPathColour);
    document.getElementById("route-plan-content").innerHTML = routePlan;
}

function checkPlanRoute() {
 
    if (origin && dest) {        
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
