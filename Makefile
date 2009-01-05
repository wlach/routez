include config.mk

default:  libroutez.so examples/testgraph \
	python/routez/tripgraph.py python/routez/_tripgraph.so \
	ruby/routez.so

include install.mk

# Always always compile with fPIC
CFLAGS += -fPIC
CXXFLAGS += -fPIC

config.mk:
	@echo "Please run ./configure. Stop."
	@exit 1

%.o: %.cc
	g++ $< -c -o $@ $(CXXFLAGS) $(PYTHON_CFLAGS) $(RUBY_CFLAGS) -I./include -g

%.o: %.cc %.h
	g++ $< -c -o $@ $(CXXFLAGS) $(PYTHON_CFLAGS) $(RUBY_CFLAGS) -I./include -g

TRIPGRAPH_OBJECTS=lib/tripgraph.o lib/trippath.o lib/tripstop.o 

# libroutez: the main library
libroutez.so: $(TRIPGRAPH_OBJECTS)
	g++ $(TRIPGRAPH_OBJECTS) -shared -o libroutez.so -fPIC -g

# python bindings
python/routez/tripgraph.py python/routez/tripgraph_wrap_py.cc: tripgraph.i
	swig -c++ -python -I./include -o python/routez/tripgraph_wrap_py.cc $<
python/routez/_tripgraph.so: libroutez.so python/routez/tripgraph_wrap_py.o
	g++ -shared -o $@ python/routez/tripgraph_wrap_py.o libroutez.so $(PYTHON_LDFLAGS) -fPIC

# ruby bindings
ruby/routez_wrap_rb.cc: routez.i tripgraph.i 
	swig -c++ -ruby -I./include  -o $@ $<

ruby/routez.so: libroutez.so ruby/routez_wrap_rb.o
	g++ -shared -o ruby/routez.so ruby/routez_wrap_rb.o libroutez.so $(RUBY_LDFLAGS) -I./include -fPIC

# stupid test program
examples/testgraph: examples/testgraph.cc libroutez.so
	g++ $< -o $@ libroutez.so -fPIC -g -I./include

clean:
	rm -f lib/*.o examples/testgraph \
	python/routez/_tripgraph.so python/routez/tripgraph.py python/routez/tripgraph_wrap_py.cc 
