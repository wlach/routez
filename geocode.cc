#include "geocoder.h"
#include <stdio.h>

using namespace std;


int main(int argc, char *argv[])
{
    GeoCoder g("test.db");

    pair<float, float> latlng = g.get_latlng(argv[1]);
    printf("%f, %f\n", latlng.first, latlng.second);

    return 0;
}
