import ctypes
import os
import sys
import time


def run_as_admin(argv=None, debug=False):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        return True
    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        arguments = argv[1:]
    else:
        arguments = argv
    argument_line = ' '.join(arguments)
    executable = sys.executable
    if debug:
        print('Command line: ', executable, argument_line)
    ret = shell32.ShellExecuteW(None, "runas", executable, argument_line, None, 1)
    if int(ret) <= 32:
        return False
    return None


if __name__ == '__main__':
    ret = run_as_admin()
    if ret is True:
        print(f'Success(ret={ret}): admin.')
        os.system('net stop w32time')
        os.system('net start w32time')
        try:
            loop = True
            while loop:
                try:
                    os.system('w32tm /resync')
                    os.system('w32tm /query /status')
                    time.sleep(60 * 15)
                except KeyboardInterrupt:
                    while True:
                        r = input('Exit program? [y/n]')
                        if r.lower() == 'y':
                            loop = False
                            break
                        elif r.lower() == 'n':
                            break
        except:
            pass
        print('Process terminated')
    elif ret is None:
        print(f'Error(ret={ret}): not admin.')
