# module used by sandbox.test.test_restricted

def _test_restricted(_getframe):
    frame =  _getframe()
    return frame.f_restricted

