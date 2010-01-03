#!/bin/sh

mkdir -p site_media/images/bus

for i in `seq 90`; do
    convert site_media/images/marker_bus.png -weight Bold -annotate +34+14 \
	$i site_media/images/bus/marker_bus_$i.png
done