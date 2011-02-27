from django.conf import settings

# neocoder is expensive to create, so import it once when this is loaded
if settings.USE_LOCAL_GEOCODER:
    print "Loading neocoder"
    import neocoder
    neocoder = neocoder.GeoCoder(settings.GEOCODER_FILE)
else:
    neocoder = None
    import re
    latlngre = re.compile("^(-?[0-9]+(\.[0-9]+)?)\ *,\ *(-?[0-9]+(\.[0-9]+)?)$")

def geocode(location_str):
    if neocoder:
        return neocoder.get_latlng(location_str)

    match = latlngre.match(location_str)
    if match:
        return (float(match.group(1)), float(match.group(3)))
    return None
