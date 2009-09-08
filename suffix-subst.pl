#!/usr/bin/perl

use strict;

# this perl script simply substitutes a set of street suffixes (and their
# mapping into our internal address mapping code) into ragel code. the main 
# point of this is to allow us to define this information in only one single 
# place (instead of scattering it all over the ragel definition).

my @suffix_mappings = (
    { type => "Avenue",
      enum => "Address::AVENUE",
      suffixes => [ "av", 
		    "ave", 
		    "aven", 
		    "avenu", 
		    "avenue", 
		    "avn", 
		    "avnue" ] },
    { type => "Boulevard",
      enum => "Address::BOULEVARD",
      suffixes => [ "blvd", 
		   "boul", 
		   "boulevard", 
		   "boulv" ] },
    { type => "Crescent",
      enum => "Address::CRESCENT",
      suffixes => [ "crecent", 
		    "cres", 
		    "crescent", 
		    "cresent", ] },
    { type => "Drive",
      enum => "Address::DRIVE",
      suffixes => [ "dr", 
		    "driv", 
		    "drive", 
		    "drives", ] },
    { type => "Highway",
      enum => "Address::HIGHWAY",
      suffixes => [ "highway",
		    "highwy",
		    "hiway",
		    "hiwy",
		    "hwy", ] },
    { type => "Lane",
      enum => "Address::LANE",
      suffixes => [ "la",
		    "lane",
		    "lanes",
		    "ln", ] },
    { type => "Road",
      enum => "Address::ROAD",
      suffixes => [ "rd",
		    "ro",
		    "road", ] },
    { type => "Rotary",
      enum => "Address::ROTARY",
      suffixes => [ "rotary", 
		    "rtry", ] },
    { type =>  "Row",
      enum => "Address::ROW",
      suffixes => [ "row", ] },
    { type => "Street",
      enum => "Address::STREET",
      suffixes => [ "st",
		    "street",
		    "streets",
		    "strt", ] },
    { type => "Terrace",
      enum => "Address::TERRACE",
      suffixes => [ "ter",
		    "terr",
		    "terrace", ] },
    );

# The main suffix expression
my $main_suffix_expression = "(" . 
    join("|", map { "suffix$_->{type}" } @suffix_mappings) . ");";

# specific, sub suffix expressions
my $suffix_subexpressions;

foreach my $suffix_mapping (@suffix_mappings) {
    my $suffix_action = "action endSuffix" . $suffix_mapping->{type} . " { " .
	"addr.suffix = $suffix_mapping->{enum}; }\n";
    my $suffixes = $suffix_mapping->{suffixes};
    my $suffix_expression = "suffix$suffix_mapping->{type} = (" .
	join("|", map { "\"$_\"i" } @$suffixes) . ") >getStartStr " . 
	"\%endSuffix$suffix_mapping->{type};\n";
    $suffix_subexpressions .= $suffix_action . $suffix_expression;
}

print "/* This file has been generated with the help of suffix-subst.pl. */\n";

while (<STDIN>) {    
    s/\@SUFFIX_SUBEXPRESSIONS\@/$suffix_subexpressions/;
    s/\@MAIN_SUFFIX_EXPRESSION\@/$main_suffix_expression/;
    print $_;
}
