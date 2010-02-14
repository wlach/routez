install-neocoder: libneocoder.so 
	$(INSTALL) -d $(DESTDIR)$(libdir)
	$(INSTALL_PROGRAM) libneocoder.so $(DESTDIR)$(libdir)/ ;

# note: this is very non-idiomatic way of installing a python library. it
# probably doesn't handle edge cases well. but it works for me.
install-python: python/neocoder/_geocoder.so python/neocoder/__init__.py
	$(INSTALL) -d $(DESTDIR)$(libdir)/python/neocoder
	$(INSTALL) python/neocoder/_geocoder.so $(DESTDIR)$(libdir)/python/neocoder
	$(INSTALL) python/neocoder/__init__.py $(DESTDIR)$(libdir)/python/neocoder

install-util: utils/creategeodb.py
	$(INSTALL) -d $(DESTDIR)$(bindir)
	$(INSTALL) utils/gml2py.py $(DESTDIR)$(bindir)
	$(INSTALL) utils/creategeodb.py $(DESTDIR)$(bindir)


install: install-neocoder install-python install-util
