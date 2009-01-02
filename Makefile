include config.mk

# Always always compile with fPIC
CFLAGS += -fPIC
CXXFLAGS += -fPIC

default: tripgraph.py _tripgraph.so testgraph

config.mk:
	@echo "Please run ./configure. Stop."
	@exit 1

%.o: %.cc
	g++ $< -c -o $@ $(CXXFLAGS) $(PYTHON_CFLAGS) -g

%.o: %.cc %.h
	g++ $< -c -o $@ $(CXXFLAGS) $(PYTHON_CFLAGS) -g

TRIPGRAPH_OBJECTS=tripgraph.o trippath.o tripstop.o tripgraph_wrap_py.o

tripgraph.py tripgraph_wrap_py.cc: tripgraph.i
	swig -c++ -python -o tripgraph_wrap_py.cc $<

_tripgraph.so: $(TRIPGRAPH_OBJECTS)
	g++ $(TRIPGRAPH_OBJECTS) -shared -o _tripgraph.so -fPIC -g

testgraph: testgraph.cc _tripgraph.so
	g++ testgraph.cc -o testgraph _tripgraph.so -fPIC $(PYTHON_LDFLAGS) $(PYTHON_CFLAGS) -g

clean:
	rm -f _tripgraph.so *.o testgraph tripgraph.py tripgraph_wrap_py.cc *~