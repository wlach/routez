include config.mk

default: latlng_ext.so

config.mk:
	@echo "Please run ./configure. Stop."
	@exit 1

latlng_ext.so: latlng.cc
	g++ latlng.cc -shared -o latlng_ext.so -fPIC $(BOOST_PYTHON_LDFLAGS) $(BOOST_PYTHON_CFLAGS)

clean:
	rm -f latlng_ext.so