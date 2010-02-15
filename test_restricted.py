# Module used by test_module_frame_restricted() from tests.py

def _test_restricted(_getframe):
    frame =  _getframe()
    return frame.f_restricted

