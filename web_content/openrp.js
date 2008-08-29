var tripListShort;
var tripListLong;
var stopList;

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
    busStopIcon.image = "small_bus_marker.png";
    busStopIcon.iconSize = new GSize(64, 52);
    busStopIcon.iconAnchor = new GPoint(5, 47);
    //  icon.infoWindowAnchor = new GPoint(5, 5);

    walkStopIcon = new GIcon();
    walkStopIcon.image = "small_walk_marker.png";
    walkStopIcon.iconSize = new GSize(30, 50);
    walkStopIcon.iconAnchor = new GPoint(5, 45);
    
    // stopIcon.shadow = "/file/mm_20_shadow.png";
    // iconBackground = makeStopIcon();
    // iconBackground.image = "/file/mm_20_blue_trans.png";
    // iconBackground.shadow = "/file/mm_20_shadow_trans.png";
}


function loadTripListCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }

    tripListShort = new Array();
    tripListLong = new Array();

    var myData = eval(data);
    for (var i=0; i<myData.length; ++i) {
        tripListShort[myData[i][0]] = myData[i][1];
        tripListLong[myData[i][0]] = myData[i][1] + " (" + myData[i][2] + ")";
    }    
}

function loadStopListCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }

    stopList = new Array();

    var myData = eval(data);

    for (var i=0; i<myData.length; ++i) {
        stopList["gtfs" + myData[i][0]] = [ myData[i][1], myData[i][2], myData[i][3] ];
    }
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

function submitCallback(data, responseCode) {
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

    var bounds = new GLatLngBounds;
    bounds.extend(origin);
    bounds.extend(dest);

    if (actions.length == 0) {
        routePlan += "We couldn't find any transit directions for this trip. ";
        routePlan += "This probably means it's faster to walk.";
        addWalkingOverlay(origin, dest);
    } else {
        for (var i=0; i<actions.length; ++i) {
            action = actions[i][0];
            var gtfs_node = actions[i][1].replace(/.*(gtfs[0-9]+)/, "$1");
            var latlng = new GLatLng(stopList[gtfs_node][1], 
                                     stopList[gtfs_node][2])
            routePath[routePath.length] = latlng;
            bounds.extend(latlng);
            if (i==(actions.length - 1)) {
                map.addOverlay(new GMarker(latlng, walkStopIcon));
            }

            if (action == "board") {
                var tripId = actions[i][1].replace(/\sat\sgtfs[0-9]+/, "");

                var markerOpts = new Object();
                markerOpts.icon = busStopIcon;
                markerOpts.labelText = tripListShort[tripId];
                markerOpts.labelClass = "tooltip";
                markerOpts.labelOffset = new GSize(24, -44);
                map.addOverlay(new LabeledMarker(latlng, markerOpts));

                routePlan += "<p><b>Board</b> the " + tripListLong[tripId];
                routePlan += " departing from " + stopList[gtfs_node][0];
                routePlan += " at " + actions[i][2] + " and travel to ";
            } else if (action == "alight") {
                var tripId = actions[i][1].replace(/\sat\sgtfs[0-9]+/, "");
                routePlan += stopList[gtfs_node][0] + ".</p>";
            }
        }
        addWalkingOverlay(origin, routePath[0]);
        addWalkingOverlay(routePath[routePath.length-1], dest);
    }
    map.setCenter(bounds.getCenter());
    var zoom = map.getBoundsZoomLevel(bounds);
    map.setCenter(bounds.getCenter(), zoom);

    var polyline = new GPolyline(routePath, "#ff0000", 5);
    map.addOverlay(polyline);
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
    }
}

function gotOriginCallback(latlng) {
    if (latlng) {
        origin = latlng;
    } else {
        alert("Google didn't understand origin!");
    }

    checkPlanRoute();
}

function gotDestCallback(latlng) {
    if (latlng) {
        dest = latlng;
    } else {
        alert("Google didn't understand destination!");
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