def testFloat(str_in):
    """
    Tests if float inputs are correct.
    """
    try:
        i = float(str_in)
    except:
        return False
    return True

def testInteger(str_in):
    """
    Tests if int inputs are correct.
    """
    try:
        i = int(str_in)
    except:
        return False
    return True
