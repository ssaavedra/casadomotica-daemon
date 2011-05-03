#!/usr/bin/python
# vim: set fileencoding=utf-8 noet ts=4 sw=4 sts=4 tw=79 :

__all__ = ["iluminacion"]

def load_all():
	runables = []
	
	for module in __all__:
		x = __import__(module)
		runables.append(x.run)
		

