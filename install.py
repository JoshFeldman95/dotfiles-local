#!/usr/bin/env python

# Script to automatically set up the environment

import sys, os, subprocess, json

INSTALL_DATA_FILE = 'install.json'

# colors
class colors:
    __tty = sys.stdout.isatty()
    NONE = ''
    MAGENTA = '\033[95m' if __tty else ''
    YELLOW = '\033[93m' if __tty else ''
    BLUE = '\033[94m' if __tty else ''
    GREEN = '\033[92m' if __tty else ''
    RED = '\033[91m' if __tty else ''
    RESET = '\033[0m' if __tty else ''

def make_color_printer(color = colors.NONE):
    def color_print(msg, end = '\n'):
        sys.stdout.write(color + msg + colors.RESET + end)
    return color_print

INFO = make_color_printer(colors.NONE)
DETAIL = make_color_printer(colors.YELLOW)
OK = make_color_printer(colors.BLUE)
SUCC = make_color_printer(colors.GREEN)
WARN = make_color_printer(colors.MAGENTA)
FAIL = make_color_printer(colors.RED)
NEWLINE = lambda: sys.stdout.write('\n')

def self_path():
    return os.path.dirname(os.path.realpath(__file__))

def exists(path):
    '''Returns true iff the path exists'''
    path = os.path.expanduser(path)
    return os.path.exists(path)

def islink(path):
    '''Returns true iff the path is a symlink'''
    return os.path.islink(os.path.expanduser(path))

def linkdest(path):
    '''Returns the absolute path to the destination of the symlink'''
    path = os.path.expanduser(path)
    reldest = os.readlink(path)
    return os.path.join(os.path.dirname(path), reldest)

def link(source, link_name):
    '''Returns true iff linking was unsuccessful'''
    unsuccessful = False
    source = os.path.join(self_path(), source)
    if not exists(link_name) and islink(link_name):
        WARN('[!] invalid link %s -> %s' % (link_name, linkdest(link_name)))
        unsuccessful = True
    elif not exists(link_name):
        OK('[*] creating link %s -> %s' % (link_name, source))
        os.symlink(source, os.path.expanduser(link_name))
    elif exists(link_name) and not islink(link_name):
        WARN('[!] %s already exists but is a regular file or directory' %
            link_name)
        unsuccessful = True
    elif not (linkdest(link_name) == source):
        WARN('[!] incorrect link %s -> %s' % (link_name, linkdest(link_name)))
        unsuccessful = True
    else:
        INFO('[ ] link exists %s -> %s' % (link_name, source))
    return unsuccessful

def process_links(links):
    unsuccessful = False
    for dest, source in links.items():
        if link(source, dest):
            unsuccessful = True
    NEWLINE()
    if unsuccessful:
        FAIL('FAILURE: some links were not successfully set up')
    else:
        SUCC('SUCCESS: all links have been set up')
    return unsuccessful

def process_shell(cmds):
    if not cmds:
        return False
    unsuccessful = False
    for cmd, msg in cmds:
        INFO('%s [' % msg, end = '')
        DETAIL('%s' % cmd, end = '')
        INFO(']... ', end = '')
        sys.stdout.flush() # force printing of above line
        ret = subprocess.call(cmd, shell = True, stdout = subprocess.PIPE,
            stderr = subprocess.PIPE, cwd = self_path())
        OK('SUCCESS') if ret == 0 else FAIL('FAILURE')
        if ret != 0:
            unsuccessful = True
    NEWLINE()
    if unsuccessful:
        FAIL('FAILURE: some tasks were not run successfully')
    else:
        SUCC('SUCCESS: all tasks executed')

def main():
    data_file_path = os.path.join(self_path(), INSTALL_DATA_FILE)
    with open(data_file_path) as data_file:
        data = json.load(data_file)
        links = data['links']
        precmds = data['precmds']
        postcmds = data['postcmds']
    pre_fail = process_shell(precmds)
    if precmds:
        NEWLINE()
    link_fail = process_links(links)
    if postcmds:
        NEWLINE()
    post_fail = process_shell(postcmds)
    NEWLINE()
    if any((pre_fail, link_fail, post_fail)):
        FAIL('FAILURE: environment has not been set up successfully')
    else:
        SUCC('SUCCESS: environment has been set up')

if __name__ == '__main__':
    main()
