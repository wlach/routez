%module geocoder

%{
#include "geocoder.h"
%}

%include "std_pair.i"
%template(LatLng) std::pair<float, float>;
%include "geocoder.h"
