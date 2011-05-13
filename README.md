## About

Routez is a transit planning web service written in Python and Javascript. 
It uses the libroutez (http://github.com/wlach/libroutez) library for trip
planning functionality.

## Setup

Install various required packages:

Ubuntu or Debian Linux (older versions e.g. 10.04 Lucid Lynx):

    sudo apt-get install -y g++ imagemagick make python-dev ruby ruby1.8-dev \
        ruby-dev swig sqlite3-dev libpcre++-dev

Ubuntu or Debian Linux (newer versions e.g. 11.04 Natty Narwhal):

    sudo apt-get install -y g++ imagemagick make python-dev ruby ruby1.8-dev \
        ruby-dev swig libsqlite3-dev libpcre++-dev

MacOS X:

Install an Apple Developer SDK (the iOS dev SDK should work fine), pcre 
(http://www.pcre.org/) and ImageMagick (easiest to install this via 
MacPorts or similar). 

Initialize git submodules from the root directory:

    git submodule init
    git submodule update

Then, in root, copy local.cfg.tmpl to local.cfg and modify it according to
your needs. It should be fairly self-explanatory how to do so-- here's the one
I use for hbus.ca:

    [buildout]
    extends = buildout.cfg
    
    [routez_settings]
    server_name = hbus.ca
    cmaps_api_key = 6cf313fb0cac592a98c0f60ab0693118
    analytics_key = UA-1648932-4
    use_local_geocoder = 1
    
    [geodata]
    gtfs_file = /Users/wlach/src/halifax-metro-transit_20101104_0800.zip
    osm_file = /Users/wlach/src/hrm-area-serviced-by-mt-3.osm
    gml_file = /Users/wlach/src/ns-geobase/NRN_NS_7_1_GEOM.gml
    
    [routez_server]
    ssh_alias = hbus
    buildout_directory = /home/routez/Sites/hbus

The only section that really demands explanation is geodata.

* gtfs_file: A general transit feed file of the region you're covering
* osm_file:  An OpenStreetMap file of the road network for the region you're
covering (can be omitted if you don't care about trip planning)
* gml_file:  A geometry markup file (as published by geobase.ca) of the region
you're covering. Canadian-specific, can be omitted for other locales (though
typing in an address will no longer work in the travel UI: you'll have to use
lat/lng coordinates directly)

Run buildout from the project's root directory:

    python bootstrap.py
    ./bin/buildout -c local.cfg

Run a script to generate the required databases:

    ./bin/createall

## Running routez

To run a test server on your workstation, simply run:

    ./bin/routez runserver

The only currently supported server configuration for routez is currently the 
Ubuntu Lucid LTS release (http://releases.ubuntu.com/lucid/) using the nginx
web server (http://nginx.org/). So install that if needed:

    sudo apt-get install -y nginx

Remove nginx's default site:

    rm /etc/nginx/sites-enabled/default

Link routez to your sites-enabled directory:

    ln -s $PWD/etc/routez-nginx.conf /etc/nginx/sites-enabled/routez

Generate static files:

    ./bin/routez collectstatic

Restart nginx:

    /etc/init.d/nginx restart

Start routez:

    ./bin/restart-routez

And you're off! You should be able to get access to routez through your site's 
IP address.
