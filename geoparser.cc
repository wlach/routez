
#line 1 "geoparser.rl"
/* This file has been generated with the help of suffix-subst.pl. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "address.h"


#line 60 "geoparser.rl"



#line 15 "geoparser.cc"
static const char _addrparser_actions[] = {
	0, 1, 0, 1, 1, 1, 2, 1, 
	3, 1, 4, 1, 5, 1, 6, 1, 
	7, 1, 8, 1, 9, 1, 10, 1, 
	11, 1, 12, 1, 13
};

static const unsigned char _addrparser_key_offsets[] = {
	0, 0, 2, 11, 18, 26, 47, 49, 
	54, 57, 60, 63, 64, 67, 69, 73, 
	75, 77, 78, 80, 82, 87, 89, 91, 
	93, 95, 97, 101, 103, 105, 107, 108, 
	113, 115, 118, 120, 123, 126, 127, 131, 
	135, 137, 139, 143, 145, 146, 150, 153, 
	155, 158, 159, 165, 166, 173, 175, 177, 
	179, 181, 182, 183, 185, 188, 192, 194, 
	196, 199, 200, 202, 204, 207, 210, 212, 
	214, 215, 218
};

static const char _addrparser_trans_keys[] = {
	48, 57, 32, 9, 13, 48, 57, 65, 
	90, 97, 122, 32, 9, 13, 65, 90, 
	97, 122, 0, 32, 9, 13, 65, 90, 
	97, 122, 32, 65, 66, 67, 68, 72, 
	76, 82, 83, 84, 97, 98, 99, 100, 
	104, 108, 114, 115, 116, 9, 13, 86, 
	118, 0, 69, 78, 101, 110, 0, 78, 
	110, 0, 85, 117, 0, 69, 101, 0, 
	0, 85, 117, 69, 101, 76, 79, 108, 
	111, 86, 118, 68, 100, 0, 85, 117, 
	76, 108, 0, 69, 86, 101, 118, 86, 
	118, 65, 97, 82, 114, 82, 114, 69, 
	101, 67, 83, 99, 115, 69, 101, 78, 
	110, 84, 116, 0, 0, 67, 69, 99, 
	101, 82, 114, 0, 73, 105, 86, 118, 
	0, 69, 101, 0, 83, 115, 0, 73, 
	87, 105, 119, 71, 87, 103, 119, 72, 
	104, 87, 119, 65, 89, 97, 121, 89, 
	121, 0, 65, 78, 97, 110, 0, 78, 
	110, 69, 101, 0, 83, 115, 0, 68, 
	79, 84, 100, 111, 116, 0, 0, 65, 
	84, 87, 97, 116, 119, 68, 100, 65, 
	97, 82, 114, 89, 121, 0, 0, 84, 
	116, 0, 82, 114, 69, 84, 101, 116, 
	69, 101, 84, 116, 0, 83, 115, 0, 
	69, 101, 82, 114, 0, 82, 114, 0, 
	65, 97, 67, 99, 69, 101, 0, 32, 
	9, 13, 0
};

static const char _addrparser_single_lengths[] = {
	0, 0, 1, 1, 2, 19, 2, 5, 
	3, 3, 3, 1, 3, 2, 4, 2, 
	2, 1, 2, 2, 5, 2, 2, 2, 
	2, 2, 4, 2, 2, 2, 1, 5, 
	2, 3, 2, 3, 3, 1, 4, 4, 
	2, 2, 4, 2, 1, 4, 3, 2, 
	3, 1, 6, 1, 7, 2, 2, 2, 
	2, 1, 1, 2, 3, 4, 2, 2, 
	3, 1, 2, 2, 3, 3, 2, 2, 
	1, 1, 0
};

static const char _addrparser_range_lengths[] = {
	0, 1, 4, 3, 3, 1, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 1, 0
};

static const short _addrparser_index_offsets[] = {
	0, 0, 2, 8, 13, 19, 40, 43, 
	49, 53, 57, 61, 63, 67, 70, 75, 
	78, 81, 83, 86, 89, 95, 98, 101, 
	104, 107, 110, 115, 118, 121, 124, 126, 
	132, 135, 139, 142, 146, 150, 152, 157, 
	162, 165, 168, 173, 176, 178, 183, 187, 
	190, 194, 196, 203, 205, 213, 216, 219, 
	222, 225, 227, 229, 232, 236, 241, 244, 
	247, 251, 253, 256, 259, 263, 267, 270, 
	273, 275, 278
};

static const char _addrparser_indicies[] = {
	0, 1, 2, 2, 3, 4, 4, 1, 
	5, 5, 6, 6, 1, 7, 8, 8, 
	9, 9, 1, 10, 11, 12, 13, 14, 
	15, 16, 17, 18, 19, 11, 12, 13, 
	14, 15, 16, 17, 18, 19, 10, 1, 
	20, 20, 1, 21, 22, 23, 22, 23, 
	1, 21, 24, 24, 1, 21, 25, 25, 
	1, 21, 26, 26, 1, 21, 1, 21, 
	27, 27, 1, 26, 26, 1, 28, 29, 
	28, 29, 1, 30, 30, 1, 31, 31, 
	1, 32, 1, 33, 33, 1, 34, 34, 
	1, 32, 35, 31, 35, 31, 1, 36, 
	36, 1, 37, 37, 1, 30, 30, 1, 
	38, 38, 1, 39, 39, 1, 40, 41, 
	40, 41, 1, 42, 42, 1, 43, 43, 
	1, 44, 44, 1, 45, 1, 45, 40, 
	42, 40, 42, 1, 46, 46, 1, 47, 
	48, 48, 1, 49, 49, 1, 47, 50, 
	50, 1, 47, 51, 51, 1, 47, 1, 
	52, 53, 52, 53, 1, 54, 55, 54, 
	55, 1, 56, 56, 1, 55, 55, 1, 
	53, 57, 53, 57, 1, 57, 57, 1, 
	58, 1, 59, 60, 59, 60, 1, 61, 
	62, 62, 1, 63, 63, 1, 61, 60, 
	60, 1, 61, 1, 64, 65, 66, 64, 
	65, 66, 1, 67, 1, 67, 68, 69, 
	70, 68, 69, 70, 1, 64, 64, 1, 
	66, 66, 1, 71, 71, 1, 72, 72, 
	1, 73, 1, 74, 1, 75, 75, 1, 
	76, 77, 77, 1, 78, 79, 78, 79, 
	1, 80, 80, 1, 81, 81, 1, 76, 
	79, 79, 1, 76, 1, 82, 82, 1, 
	83, 83, 1, 84, 85, 85, 1, 84, 
	86, 86, 1, 87, 87, 1, 88, 88, 
	1, 84, 1, 5, 5, 1, 1, 0
};

static const char _addrparser_trans_targs[] = {
	2, 0, 3, 2, 73, 3, 4, 74, 
	5, 4, 5, 6, 14, 24, 32, 38, 
	45, 50, 59, 66, 7, 74, 8, 12, 
	9, 10, 11, 13, 15, 18, 16, 17, 
	74, 19, 20, 21, 22, 23, 25, 26, 
	27, 31, 28, 29, 30, 74, 33, 74, 
	34, 35, 36, 37, 39, 43, 40, 42, 
	41, 44, 74, 46, 49, 74, 47, 48, 
	51, 52, 55, 74, 53, 54, 58, 56, 
	57, 74, 74, 60, 74, 61, 62, 65, 
	63, 64, 67, 68, 74, 69, 70, 71, 
	72
};

static const char _addrparser_trans_actions[] = {
	1, 0, 3, 0, 3, 0, 1, 5, 
	5, 0, 0, 1, 1, 1, 1, 1, 
	1, 1, 1, 1, 0, 7, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	9, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 11, 0, 13, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 15, 0, 0, 17, 0, 0, 
	0, 0, 0, 19, 0, 0, 0, 0, 
	0, 21, 23, 0, 25, 0, 0, 0, 
	0, 0, 0, 0, 27, 0, 0, 0, 
	0
};

static const int addrparser_start = 1;
static const int addrparser_first_final = 74;
static const int addrparser_error = 0;

static const int addrparser_en_main = 1;


#line 63 "geoparser.rl"

int main( int argc, char **argv )
{
    int cs, res = 0;
    if ( argc > 1 ) {
        Address addr;
	char *sp = NULL;
	char *ep = NULL;

        char *p = argv[1];
        char *pe = p + strlen( p ) + 1;
	char *eof = NULL;
        
#line 195 "geoparser.cc"
	{
	cs = addrparser_start;
	}

#line 76 "geoparser.rl"
        
#line 202 "geoparser.cc"
	{
	int _klen;
	unsigned int _trans;
	const char *_acts;
	unsigned int _nacts;
	const char *_keys;

	if ( p == pe )
		goto _test_eof;
	if ( cs == 0 )
		goto _out;
_resume:
	_keys = _addrparser_trans_keys + _addrparser_key_offsets[cs];
	_trans = _addrparser_index_offsets[cs];

	_klen = _addrparser_single_lengths[cs];
	if ( _klen > 0 ) {
		const char *_lower = _keys;
		const char *_mid;
		const char *_upper = _keys + _klen - 1;
		while (1) {
			if ( _upper < _lower )
				break;

			_mid = _lower + ((_upper-_lower) >> 1);
			if ( (*p) < *_mid )
				_upper = _mid - 1;
			else if ( (*p) > *_mid )
				_lower = _mid + 1;
			else {
				_trans += (_mid - _keys);
				goto _match;
			}
		}
		_keys += _klen;
		_trans += _klen;
	}

	_klen = _addrparser_range_lengths[cs];
	if ( _klen > 0 ) {
		const char *_lower = _keys;
		const char *_mid;
		const char *_upper = _keys + (_klen<<1) - 2;
		while (1) {
			if ( _upper < _lower )
				break;

			_mid = _lower + (((_upper-_lower) >> 1) & ~1);
			if ( (*p) < _mid[0] )
				_upper = _mid - 2;
			else if ( (*p) > _mid[1] )
				_lower = _mid + 2;
			else {
				_trans += ((_mid - _keys)>>1);
				goto _match;
			}
		}
		_trans += _klen;
	}

_match:
	_trans = _addrparser_indicies[_trans];
	cs = _addrparser_trans_targs[_trans];

	if ( _addrparser_trans_actions[_trans] == 0 )
		goto _again;

	_acts = _addrparser_actions + _addrparser_trans_actions[_trans];
	_nacts = (unsigned int) *_acts++;
	while ( _nacts-- > 0 )
	{
		switch ( *_acts++ )
		{
	case 0:
#line 9 "geoparser.rl"
	{
    	   sp = p; 
	   printf("sp=%p\n", sp);
    }
	break;
	case 1:
#line 13 "geoparser.rl"
	{
    	   std::string num_str;
	   num_str.assign(sp, (p-sp));
	   addr.number = atoi(num_str.c_str());
    }
	break;
	case 2:
#line 18 "geoparser.rl"
	{
    	   addr.street.assign(sp, (p-sp));
    }
	break;
	case 3:
#line 21 "geoparser.rl"
	{ addr.suffix = Address::AVENUE; }
	break;
	case 4:
#line 23 "geoparser.rl"
	{ addr.suffix = Address::BOULEVARD; }
	break;
	case 5:
#line 25 "geoparser.rl"
	{ addr.suffix = Address::CRESCENT; }
	break;
	case 6:
#line 27 "geoparser.rl"
	{ addr.suffix = Address::DRIVE; }
	break;
	case 7:
#line 29 "geoparser.rl"
	{ addr.suffix = Address::HIGHWAY; }
	break;
	case 8:
#line 31 "geoparser.rl"
	{ addr.suffix = Address::LANE; }
	break;
	case 9:
#line 33 "geoparser.rl"
	{ addr.suffix = Address::ROAD; }
	break;
	case 10:
#line 35 "geoparser.rl"
	{ addr.suffix = Address::ROTARY; }
	break;
	case 11:
#line 37 "geoparser.rl"
	{ addr.suffix = Address::ROW; }
	break;
	case 12:
#line 39 "geoparser.rl"
	{ addr.suffix = Address::STREET; }
	break;
	case 13:
#line 41 "geoparser.rl"
	{ addr.suffix = Address::TERRACE; }
	break;
#line 341 "geoparser.cc"
		}
	}

_again:
	if ( cs == 0 )
		goto _out;
	if ( ++p != pe )
		goto _resume;
	_test_eof: {}
	_out: {}
	}

#line 77 "geoparser.rl"

	printf("address num %d street %s suffixId: %d\n", addr.number, addr.street.c_str(), addr.suffix);
    }
    printf("result = %d\n", res );
    return 0;
}
