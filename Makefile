default: tests/geocode

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) -D WVTEST_CONFIGURED -I./include -I./wvtest/cpp -g
	@g++ $< -MM $(CXXFLAGS) -D WVTEST_CONFIGURED -I./include -I./wvtest/cpp > $*.d
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
GEOCODER_OBJS=$(patsubst %,lib/%,geocoder.o geoparser.o address.o)
GEOCODE_OBJS= $(GEOCODER_OBJS) tests/geocode.o
tests/geocode: $(GEOCODE_OBJS) 
	echo $(GEOCODE_OBJS) 
	g++ $(GEOCODE_OBJS) $(LDFLAGS) -o $@

TEST_OBJS=t/geoparser.t.o
WVTEST_OBJS=$(patsubst %,wvtest/cpp/%, wvtest.o wvtestmain.o)
t/all.t: $(TEST_OBJS) $(WVTEST_OBJS) $(GEOCODER_OBJS)
	g++ $(TEST_OBJS) $(WVTEST_OBJS) $(GEOCODER_OBJS) $(LDFLAGS) -o $@ -fPIC -g

test: t/all.t
	LD_LIBRARY_PATH=$(PWD) valgrind --tool=memcheck wvtest/wvtestrun t/all.t


clean:
	rm -f *.so *.d lib/*.o lib/*.d lib/address.cc lib/geoparser.cc \
	utils/*.o utils/*.d utils/geocode

-include $(GEOPARSER_OBJS:.o=.d)
