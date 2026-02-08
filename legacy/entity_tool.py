import os

def change_mode(path, mode):
    mode_new = int(str(mode), 8)
    mode_old = os.stat(path).st_mode & 0o777
    mode_old_oct = oct(mode_old)
    os.chmod(path, mode_new)
    mode_new_oct = oct(mode_new)
    return mode_old_oct, mode_new_oct