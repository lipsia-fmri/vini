"""
Turn on/off printing stuff with verboseprint
"""

verbose = False
if verbose:
    def verboseprint(*args):
        for arg in args:
           print(arg),
        print
else:
    verboseprint = lambda *a: None
