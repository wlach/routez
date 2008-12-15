var routeListShort;
var routeListLong;
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


function loadRouteListCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }

    routeListShort = new Array();
    routeListLong = new Array();

    var myData = eval(data);
    for (var i=0; i<myData.length; ++i) {
        route = myData[i];
        routeListShort[route['id']] = route['shortname'];
        routeListLong[route['id']] = route['shortname'] + " (" +  route['longname'] + ")";
    }    
}

function loadStopListCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }

    stopList = new Array();

    var myData = eval(data);

    for (var i=0; i<myData.length; ++i) {
        var stop = myData[i];
        stopList[stop['id']] = stop;
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

    var bounds = new GLatLngBounds;
    bounds.extend(origin);
    bounds.extend(dest);

    if (actions.length == 0) {
        routePlan += "We couldn't find any transit directions for this trip. ";
        routePlan += "This probably means it's faster to walk.";
        addWalkingOverlay(origin, dest);
    } else {
        for (var i=0; i<actions.length; ++i) {
            if (actions[i].type == "alight" || actions[i].type == "pass") {
                var latlng = new GLatLng(actions[i].lat, 
                                         actions[i].lng)
                routePath[routePath.length] = latlng;
                bounds.extend(latlng);
            }

            if (actions[i].type == "board") {
                var id = actions[i].id;
                var routeId = actions[i].route_id;

                var markerOpts = new Object();
                markerOpts.icon = busStopIcon;
                markerOpts.labelText = routeListShort[routeId];
                markerOpts.labelClass = "tooltip";
                markerOpts.labelOffset = new GSize(24, -44);
                map.addOverlay(new LabeledMarker(latlng, markerOpts));
                
                routePlan += "<p><b>Board</b> the " + routeListLong[routeId];
                routePlan += " departing from " + stopList[id].name;
                routePlan += " at " + actions[i].time + " and travel to ";
            } else if (actions[i].type == "alight") {
                var previd = actions[i-1].dest_id;
                routePlan += stopList[previd].name + ".</p>";
            } 
            
            // if we have to get off and walk, show a nice icon
            if (i>0 && actions[i-1].type == "alight" && 
                actions[i].type != "board") {
                map.addOverlay(new GMarker(latlng, walkStopIcon));
            }

            if (i==(actions.length-1)) {
                routePlan += "<p><b>Arrive</b> at " + actions[i].time +".</p>";
            }
        }
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