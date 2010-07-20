#!/usr/bin/env python
""" ---*< mysqlbackup.py >*---------------------------------------------------

Simple MySQL export + encrypt

Copyright (C) 2010 st0w <st0w@st0w.com> * http://github.com/st0w

This is released under the MIT License... Do with this whatever the
hell you want, I don't care.

Created on Jul 18, 2010

Dumps all tables/schemas in MySQL to a compressed, GnuPG-encrypted file
suitable for daily exports.  Does not store unencrypted data on disk at
all.

Setup:

You should ideally run this under a user created specifically for this
task.  The user should not be able to login regularly, and his home
directory should be set mode 700.  In the setup below, the local user
I am running as is 'sqlback' and I have setup a MySQL user "_sqlback"
specifically for backups.  I've granted that user *ONLY* SELECT and
LOCK TABLES permissions on *.*.  These are the only perms needed to run
a backup.

You'll then need to store the password for the MySQL user (_sqlback) in
the file ".my.cnf: in the local user's (sqlback) home directory that is
running this.  Make sure you set perms on .my.cnf to 400 or 600 so that
nobody can read it.

I then have a cron job setup as follows to run once daily::
    #!/bin/bash
    (HOME=/home/sqlback su -m sqlback -c /home/sqlback/mysqlbackup.py)

Finally, set the variables below to appropriate values for you.

"""
# ---*< Standard imports >*---------------------------------------------------
import bz2
from datetime import date
import gnupg
import os
import shlex
import stat
import subprocess
import sys
from tempfile import mkstemp
from time import time

# ---*< Third-party imports >*------------------------------------------------

# ---*< Local imports >*------------------------------------------------------

# ---*< Initialization >*-----------------------------------------------------
BACKUPDIR = '/dir/to/write/backup/files'
MYSQLDUMP = '/usr/bin/mysqldump'
GPGKEYRING = '/home/sqlback/.gnupg'

"""keyid of user to encrypt data to"""
KEYID = 'PUT YOUR KEYID HERE'

"""MySQL user details - needs SELECT and LOCK TABLES perms"""
USER = '_sqlback'

DEBUG = False

# ---*< Code >*---------------------------------------------------------------
def debug(msg):
    """Just a simple debug wrapper.  Set DEBUG=True above for output"""
    if DEBUG:
        sys.stderr.write(msg)

def do_backup(username=USER):
    """Dump data from MySQL, encrypt it, compress it"""
    gpg = gnupg.GPG(gnupghome=GPGKEYRING)

    """Call mysqldump and get all data into a string"""
    mysqldump = subprocess.Popen(shlex.split("%s -u %s -A" %
                                             (MYSQLDUMP, username)),
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)

    stdoutdata = mysqldump.communicate()[0]
    debug('Compressing %s bytes of data...\n' % len(stdoutdata))

    """Compress the string using bzip2"""
    compressed = bz2.compress(stdoutdata)

    """Encrypt it using gpg"""
    debug('Encrypting %s bytes of compressed data...\n' % len(compressed))
    encrypted = gpg.encrypt(compressed, [KEYID, ], armor=False)

    debug('Writing %s bytes of compressed+encrypted data..\n' %
          len(str(encrypted)))

    prefix = 'mysql-%s-' % date.fromtimestamp(time()).isoformat()
    (fd, fn) = mkstemp(dir=BACKUPDIR, prefix=prefix, suffix='.bz2.gpg')
    os.write(fd, str(encrypted))
    os.close(fd)
    os.chmod(fn, stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP)
    debug('Data written to %s\n' % fn)

if __name__ == "__main__":
    if os.geteuid() == 0:
        sys.stderr.write("Don't run this as root.  There's no point and it's "
                         "a bad security move.  Refusing to run, exiting.\n")
        sys.exit(1)

    do_backup()
