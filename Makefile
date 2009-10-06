default: tests/geocode

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) -I./include -g
	@g++ $< -MM $(CXXFLAGS) -I./include > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

lib/geoparser.cc: lib/geoparser.cc.in gen-address-cc.pl
	perl gen-address-cc.pl < $< > $@

lib/address.cc: lib/address.cc.in gen-address-cc.pl
	perl gen-address-cc.pl < $< > $@

CPPFLAGS=-I./include
LDFLAGS=-lsqlite3 -lboost_regex
GEOCODE_OBJS=$(patsubst %,lib/%,geocoder.o geoparser.o address.o) tests/geocode.o
tests/geocode: $(GEOCODE_OBJS) 
	echo $(GEOCODE_OBJS) 
	g++ $(GEOCODE_OBJS) $(LDFLAGS) -o $@

clean:
	rm -f *.so *.d lib/*.o lib/*.d lib/address.cc lib/geoparser.cc \
	utils/*.o utils/*.d utils/geocode

-include $(GEOPARSER_OBJS:.o=.d)
