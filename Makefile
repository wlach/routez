include config.mk

default: tripgraph.so testgraph

config.mk:
	@echo "Please run ./configure. Stop."
	@exit 1

%.o: %.cc %.h
	g++ $< -c -o $@ $(BOOST_PYTHON_CFLAGS) -g

TRIPGRAPH_OBJECTS=tripgraph.o trippath.o tripstop.o

tripgraph.so: $(TRIPGRAPH_OBJECTS)
	g++ $(TRIPGRAPH_OBJECTS) -shared -o tripgraph.so -fPIC $(BOOST_PYTHON_LDFLAGS) $(BOOST_PYTHON_CFLAGS) -g

testgraph: testgraph.cc tripgraph.so
	g++ testgraph.cc -o testgraph tripgraph.so -fPIC $(BOOST_PYTHON_LDFLAGS) $(BOOST_PYTHON_CFLAGS) -g

clean:
	rm -f tripgraph.so *.o testgraph *~