#include "geocoder.h"
#include <stdio.h>

using namespace std;


int main(int argc, char *argv[])
{
    if (argc < 3)
    {
        printf("USAGE: %s <geodb> <expression>\n", argv[0]);
        return 1;
    }

    GeoCoder g(argv[1]);

    pair<float, float> *latlng = g.get_latlng(argv[2]);
    if (latlng)
        printf("%f, %f\n", latlng->first, latlng->second);
    else
        printf("Couldn't geocode location.\n");

    return 0;
}
