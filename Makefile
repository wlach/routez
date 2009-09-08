default: geoparser

%.o: %.cc 
	g++ $< -c -o $@ $(CXXFLAGS) -I./include -g
	@g++ $< -MM $(CXXFLAGS) -I./include > $*.d
	@mv -f $*.d $*.d.tmp
	@sed -e 's|.*:|$*.o:|' < $*.d.tmp > $*.d
	@sed -e 's/.*://' -e 's/\\$$//' < $*.d.tmp | fmt -1 | \
	  sed -e 's/^ *//' -e 's/$$/:/' >> $*.d
	@rm -f $*.d.tmp

geoparser.pdf: geoparser.rl
	ragel -Vp -o geoparser.dot geoparser.rl
	dot -Tpdf -o geoparser.pdf geoparser.dot 

geoparser.rl: geoparser.rl.in suffix-subst.pl
	perl suffix-subst.pl < $< > $@

geoparser.cc: geoparser.rl
	ragel geoparser.rl -o $@

address_suffixes.cc: address_suffixes.cc.in suffix-subst.pl
	perl suffix-subst.pl < $< > $@

GEOPARSER_OBJS=geoparser.o address.o address_suffixes.o 

geoparser: $(GEOPARSER_OBJS)
	g++ $(GEOPARSER_OBJS) $(LDFLAGS) -o $@

clean:
	rm -f *.so *.d *.o *~ geoparser.dot geoparser.pdf address_suffixes.cc \
	geoparser.rl geoparser