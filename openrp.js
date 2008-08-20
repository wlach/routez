var tripList;
var stopList;

var origin = null;
var dest = null;

var map;
var geocoder;

function loadTripListCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }

    tripList = new Array();

    var myData = eval(data);
    for (var i=0; i<myData.length; ++i) {
        tripList[myData[i][0]] = myData[i][1] + " (" + myData[i][2] + ")";
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

function submitCallback(data, responseCode) {
    if (responseCode != 200) {
        return;
    }
    
    actions = eval(data);
    var routePlan = "";
    var routePath = new Array();
    for (var i=0; i<actions.length; ++i) {
        action = actions[i][0];
        var gtfs_node = actions[i][1].replace(/.*(gtfs[0-9]+)/, "$1");
        routePath[routePath.length] = new GLatLng(stopList[gtfs_node][1], 
                                                  stopList[gtfs_node][2]);

        if (action == "board" || action == "alight") {
            routePlan += "<p><b>" + action + "</b> ";
            var tripId = actions[i][1].replace(/\sat\sgtfs[0-9]+/, "");
            routePlan += "on (" + tripList[tripId] + ") ";
            routePlan += "at (" + stopList[gtfs_node][0] + ") ";
            routePlan += "at " + actions[i][2] + "</p>";
        }
    }

    var polyline = new GPolyline(routePath, "#ff0000", 3);
    map.addOverlay(polyline);
    document.getElementById("moo").innerHTML = routePlan;
}

function checkPlanRoute() {
 
    if (origin && dest) {
        url = "/json/routeplan" + 
        "?startlat=" + origin.lat() + "&startlng=" + origin.lng() +
        "&endlat=" + dest.lat() + "&endlng=" + dest.lng();
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

    geocoder.getLatLng(document.getElementById('routePlanStart').value, gotOriginCallback);
    geocoder.getLatLng(document.getElementById('routePlanEnd').value, gotDestCallback);
}