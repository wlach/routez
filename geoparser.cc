
#line 1 "geoparser.rl"
/* This file has been automatically generated by suffix-subst.pl. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "address.h"


#line 37 "geoparser.rl"



#line 15 "geoparser.cc"
static const char _addrparser_actions[] = {
	0, 1, 0, 1, 1, 1, 2, 1, 
	3
};

static const char _addrparser_key_offsets[] = {
	0, 0, 2, 11, 18, 26, 38, 39, 
	42, 44, 46, 48, 49, 51, 52, 54, 
	55, 56, 57, 58, 61, 62, 63, 64, 
	65, 66, 68, 69, 70, 71, 74, 75, 
	77, 78, 80, 82, 84, 86, 87, 88, 
	90, 91, 93, 95, 96, 99, 103, 104, 
	105, 106, 108, 110, 111, 112, 113, 114, 
	116, 118, 119, 122
};

static const char _addrparser_trans_keys[] = {
	48, 57, 32, 9, 13, 48, 57, 65, 
	90, 97, 122, 32, 9, 13, 65, 90, 
	97, 122, 0, 32, 9, 13, 65, 90, 
	97, 122, 32, 97, 98, 99, 100, 104, 
	108, 114, 115, 116, 9, 13, 118, 0, 
	101, 110, 0, 110, 0, 117, 0, 101, 
	0, 0, 117, 101, 108, 111, 118, 100, 
	117, 108, 0, 101, 118, 118, 97, 114, 
	114, 101, 99, 115, 101, 110, 116, 0, 
	99, 101, 114, 0, 105, 118, 0, 101, 
	0, 115, 105, 119, 103, 119, 104, 119, 
	97, 121, 121, 97, 110, 0, 110, 101, 
	100, 111, 116, 0, 97, 116, 119, 97, 
	114, 116, 0, 114, 101, 116, 101, 116, 
	101, 114, 0, 114, 0, 97, 99, 32, 
	9, 13, 0
};

static const char _addrparser_single_lengths[] = {
	0, 0, 1, 1, 2, 10, 1, 3, 
	2, 2, 2, 1, 2, 1, 2, 1, 
	1, 1, 1, 3, 1, 1, 1, 1, 
	1, 2, 1, 1, 1, 3, 1, 2, 
	1, 2, 2, 2, 2, 1, 1, 2, 
	1, 2, 2, 1, 3, 4, 1, 1, 
	1, 2, 2, 1, 1, 1, 1, 2, 
	2, 1, 1, 0
};

static const char _addrparser_range_lengths[] = {
	0, 1, 4, 3, 3, 1, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 1, 0
};

static const unsigned char _addrparser_index_offsets[] = {
	0, 0, 2, 8, 13, 19, 31, 33, 
	37, 40, 43, 46, 48, 51, 53, 56, 
	58, 60, 62, 64, 68, 70, 72, 74, 
	76, 78, 81, 83, 85, 87, 91, 93, 
	96, 98, 101, 104, 107, 110, 112, 114, 
	117, 119, 122, 125, 127, 131, 136, 138, 
	140, 142, 145, 148, 150, 152, 154, 156, 
	159, 162, 164, 167
};

static const char _addrparser_indicies[] = {
	0, 1, 2, 2, 3, 4, 4, 1, 
	5, 5, 6, 6, 1, 7, 8, 8, 
	9, 9, 1, 10, 11, 12, 13, 14, 
	15, 16, 17, 18, 19, 10, 1, 20, 
	1, 21, 22, 23, 1, 21, 24, 1, 
	21, 25, 1, 21, 26, 1, 21, 1, 
	21, 27, 1, 26, 1, 28, 29, 1, 
	30, 1, 26, 1, 31, 1, 32, 1, 
	21, 33, 26, 1, 34, 1, 35, 1, 
	30, 1, 36, 1, 37, 1, 38, 39, 
	1, 40, 1, 41, 1, 26, 1, 21, 
	38, 40, 1, 42, 1, 21, 43, 1, 
	44, 1, 21, 45, 1, 21, 26, 1, 
	46, 47, 1, 48, 49, 1, 50, 1, 
	49, 1, 47, 26, 1, 26, 1, 51, 
	26, 1, 21, 52, 1, 45, 1, 26, 
	53, 54, 1, 21, 30, 55, 26, 1, 
	54, 1, 47, 1, 56, 1, 21, 57, 
	1, 58, 26, 1, 59, 1, 45, 1, 
	60, 1, 61, 1, 21, 62, 1, 21, 
	63, 1, 27, 1, 5, 5, 1, 1, 
	0
};

static const char _addrparser_trans_targs[] = {
	2, 0, 3, 2, 58, 3, 4, 59, 
	5, 4, 5, 6, 14, 23, 30, 35, 
	41, 44, 48, 53, 7, 59, 8, 12, 
	9, 10, 11, 13, 15, 17, 16, 18, 
	19, 20, 21, 22, 24, 25, 26, 29, 
	27, 28, 31, 32, 33, 34, 36, 40, 
	37, 39, 38, 42, 43, 45, 47, 46, 
	49, 50, 51, 52, 54, 55, 56, 57
};

static const char _addrparser_trans_actions[] = {
	1, 0, 3, 0, 3, 0, 1, 5, 
	5, 0, 0, 1, 1, 1, 1, 1, 
	1, 1, 1, 1, 0, 7, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0, 
	0, 0, 0, 0, 0, 0, 0, 0
};

static const int addrparser_start = 1;
static const int addrparser_first_final = 59;
static const int addrparser_error = 0;

static const int addrparser_en_main = 1;


#line 40 "geoparser.rl"

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
        
#line 152 "geoparser.cc"
	{
	cs = addrparser_start;
	}

#line 53 "geoparser.rl"
        
#line 159 "geoparser.cc"
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
	{
    	   std::string suffix_str;
	   suffix_str.assign(sp, (p-sp));
	   addr.suffix = get_typesuffix(suffix_str);
	   printf("suffix str: %s\n", suffix_str.c_str());
    }
	break;
#line 263 "geoparser.cc"
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

#line 54 "geoparser.rl"

	printf("address num %d street %s suffixId: %d\n", addr.number, addr.street.c_str(), addr.suffix);
    }
    printf("result = %d\n", res );
    return 0;
}
