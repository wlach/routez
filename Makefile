default: geocode

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) -I./include -g
	@g++ $< -MM $(CXXFLAGS) -I./include > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

geoparser.cc: geoparser.cc.in gen-address-cc.pl
	perl gen-address-cc.pl < $< > $@

address.cc: address.cc.in gen-address-cc.pl
	perl gen-address-cc.pl < $< > $@

LDFLAGS=-lsqlite3 -lboost_regex
GEOCODE_OBJS=geocoder.o geoparser.o address.o geocode.o
geocode: $(GEOCODE_OBJS)
	g++ $(GEOCODE_OBJS) $(LDFLAGS) -o $@

clean:
	rm -f *.so *.d *.o *~ address.cc geoparser

-include $(GEOPARSER_OBJS:.o=.d)
