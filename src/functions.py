# standard
import os
import sys
# internal
from src import mem
from src import console
from src import settings
from src.snap import Snap
from src import db_backends


def load_databases():
    databases = list()
    for db in settings.DATABASES:
        backend = None
        dbms = db['dbms']
        if dbms == 'mssql':
            backend = db_backends.MSSQL
        elif dbms == 'sqlite':
            backend = db_backends.SQLite
        elif dbms == 'mysql':
            pass
        if backend and backend.check_conf(**db):
            databases.append(backend(**db))
    return databases


def load_snaps():
    snaps = list()
    for content in os.listdir(settings.SNAP_DIR):
        if content.startswith('Snap__'):
            snaps.append(Snap.from_pickle(os.path.join(settings.SNAP_DIR, content)))
    return snaps


def clear_console():
    if 'win' in sys.platform.lower():
        os.system('cls')
        return
    os.system('clear')
