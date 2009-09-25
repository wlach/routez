#!/usr/bin/perl

use strict;

# this perl script simply substitutes a set of street suffixes (and their
# mapping into our internal address mapping code) into ragel code. the main 
# point of this is to allow us to define this information in only one single 
# place (instead of scattering it all over the ragel definition).

my @suffix_mappings = (
    { type => "Avenue",
      enum => "Address::AVENUE",
      names => [ "av", 
		    "ave", 
		    "aven", 
		    "avenu", 
		    "avenue", 
		    "avn", 
		    "avnue" ] },
    { type => "Boulevard",
      enum => "Address::BOULEVARD",
      names => [ "blvd", 
		   "boul", 
		   "boulevard", 
		   "boulv" ] },
    { type => "Crescent",
      enum => "Address::CRESCENT",
      names => [ "crecent", 
		    "cres", 
		    "crescent", 
		    "cresent", ] },
    { type => "Drive",
      enum => "Address::DRIVE",
      names => [ "dr", 
		    "driv", 
		    "drive", 
		    "drives", ] },
    { type => "Highway",
      enum => "Address::HIGHWAY",
      names => [ "highway",
		    "highwy",
		    "hiway",
		    "hiwy",
		    "hwy", ] },
    { type => "Lane",
      enum => "Address::LANE",
      names => [ "la",
		    "lane",
		    "lanes",
		    "ln", ] },
    { type => "Road",
      enum => "Address::ROAD",
      names => [ "rd",
		    "ro",
		    "road", ] },
    { type => "Rotary",
      enum => "Address::ROTARY",
      names => [ "rotary", 
		    "rtry", ] },
    { type =>  "Row",
      enum => "Address::ROW",
      names => [ "row", ] },
    { type => "Street",
      enum => "Address::STREET",
      names => [ "st",
		    "street",
		    "streets",
		    "strt", ] },
    { type => "Terrace",
      enum => "Address::TERRACE",
      names => [ "ter",
		    "terr",
		    "terrace", ] },
    );

my @direction_mappings = (
    { enum => "Address::NORTH",
      names => [ "n", "north" ] },
    { enum => "Address::NORTHEAST",
      names => [ "ne", "northeast", "north east" ] },
    { enum => "Address::EAST",
      names => [ "e", "east" ] },
    { enum => "Address::SOUTHEAST",
      names => [ "se", "southeast", "south east" ] },
    { enum => "Address::SOUTH",
      names => [ "s", "south" ] }, 
    { enum => "Address::SOUTHWEST",
      names => [ "sw", "southwest", "south west" ] },
    { enum => "Address::WEST",
      names => [ "w", "west" ] }, 
    { enum => "Address::NORTHWEST",
      names => [ "nw", "northwest", "north west" ] },
    );

sub read_mappings {
    my $mappings = pop (@_);

    my $expression; my $logic;

    my $first_mapping = 1;
    foreach my $mapping (@$mappings) {
	my $names = $mapping->{names};
	if (!$first_mapping) {
	    $logic .= "else ";
	    $expression .= "|";
	} else {
	    $first_mapping = 0;
	}
	
	$expression .= join("|", @$names);
	$logic .= "if (";
	
	my $first_suffix = 1;
	foreach my $suffix (@$names) {
	    if (!$first_suffix) {
		$logic .= " || ";
	    } else {
		$first_suffix = 0;
	    }
	    
	    $logic .= "!strcasecmp(str.c_str(), \"$suffix\")";
	}
	$logic .= ")\nreturn $mapping->{enum};\n";   
    }

    return ($expression, $logic);
}

my ($suffix_expression, $suffix_logic) = read_mappings(\@suffix_mappings);
my ($direction_expression, $direction_logic) = read_mappings(\@direction_mappings);

print "/* This file has been generated with the help of suffix-subst.pl. */\n";

while (<STDIN>) {    
    s/\@SUFFIX_EXPRESSION\@/$suffix_expression/;
    s/\@SUFFIX_LOGIC\@/$suffix_logic/;
    s/\@DIRECTION_EXPRESSION\@/$direction_expression/;
    s/\@DIRECTION_LOGIC\@/$direction_logic/;
    print $_;
}
