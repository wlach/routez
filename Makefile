default: geoparser

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) -I./include -g
	@g++ $< -MM $(CXXFLAGS) -I./include > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

address.cc: address.cc.in gen-address-cc.pl
	perl gen-address-cc.pl < $< > $@

GEOPARSER_OBJS=geoparser.o address.o
LDFLAGS=-lboost_regex

geoparser: $(GEOPARSER_OBJS)
	g++ $(GEOPARSER_OBJS) $(LDFLAGS) -o $@

clean:
	rm -f *.so *.d *.o *~ address.cc geoparser