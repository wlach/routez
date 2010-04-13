-include config.mk

default: libneocoder.so tests/geocode utils/creategeodb.py \
	python/neocoder/__init__.py python/neocoder/_geocoder.so

include install.mk

# Always always compile with fPIC
CFLAGS += -fPIC
CXXFLAGS += -fPIC

# Various things we need
CXXFLAGS+=-I./include
LDFLAGS+=-lsqlite3 -lpcrecpp

# libneocoder should be a shared library 
ifeq (${OS},MACOS)
	LIBNEOCODER_LDFLAGS += -dynamiclib
else
	LIBNEOCODER_LDFLAGS += -shared
endif


config.mk:
	@echo "Please run ./configure. Stop."
	@exit 1

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) $(PYTHON_CFLAGS) -D WVTEST_CONFIGURED -I./include -I./wvtest/cpp -g
	@g++ $< -MM $(CXXFLAGS) $(PYTHON_CFLAGS) -D WVTEST_CONFIGURED -I./include -I./wvtest/cpp > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

lib/geoparser.cc: lib/geoparser.cc.in gen-address.pl
	perl gen-address.pl < $< > $@

lib/address.cc: lib/address.cc.in gen-address.pl
	perl gen-address.pl < $< > $@

utils/mappings.py: utils/mappings.py.in gen-address.pl
	perl gen-address.pl < $< > $@

utils/creategeodb.py: utils/mappings.py

GEOCODER_OBJS=$(patsubst %,lib/%,geocoder.o geoparser.o address.o)
GEOCODE_OBJS= $(GEOCODER_OBJS) tests/geocode.o
tests/geocode: $(GEOCODE_OBJS)
	g++ $(GEOCODE_OBJS) $(LDFLAGS) -o $@

libneocoder.so: $(GEOCODER_OBJS)
	g++ $(GEOCODER_OBJS) $(LDFLAGS) $(LIBNEOCODER_LDFLAGS) -o $@ -fPIC -g

python/neocoder/__init__.py python/neocoder/geocoder_wrap_py.cc: neocoder.i
	swig -classic -c++ -python -I./include -outdir python/neocoder -o python/neocoder/geocoder_wrap_py.cc $<
	mv python/neocoder/geocoder.py python/neocoder/__init__.py
python/neocoder/_geocoder.so: libneocoder.so python/neocoder/geocoder_wrap_py.o
	g++ -o $@ python/neocoder/geocoder_wrap_py.o libneocoder.so $(LDFLAGS) $(LIBNEOCODER_LDFLAGS) $(PYTHON_LDFLAGS) -fPIC

TEST_OBJS=t/geoparser.t.o
WVTEST_OBJS=$(patsubst %,wvtest/cpp/%, wvtest.o wvtestmain.o)
t/all.t: $(TEST_OBJS) $(WVTEST_OBJS) $(GEOCODER_OBJS)
	g++ $(TEST_OBJS) $(WVTEST_OBJS) $(GEOCODER_OBJS) $(LDFLAGS) -o $@ -fPIC -g

test: t/all.t
	LD_LIBRARY_PATH=$(PWD) valgrind --tool=memcheck wvtest/wvtestrun t/all.t


clean:
	rm -f *.so *.d lib/*.o lib/*.d lib/address.cc lib/geoparser.cc \
	utils/*.o utils/*.d utils/geocode libneocoder.so

-include $(GEOPARSER_OBJS:.o=.d)
-include $(TEST_OBJS:.o=.d)
