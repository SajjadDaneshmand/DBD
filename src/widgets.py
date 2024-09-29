# internal
import os
import shutil

import pandas
from src import mem
from src import console
from src import settings
from src.snap import Snap
from src import functions as fn


class BaseWidget(object):
    """BaseWidgets"""
    CODE = 0
    NAME = 'Base'
    PARENT = 0

    def __init__(self):
        self._parent = None
        self._childs = list()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, w):
        self._parent = w

    @property
    def childs(self):
        return self._childs

    def add_child(self, w):
        self._childs.append(w)

    def remove_child(self, w):
        self._childs.remove(w)

    def do(self):
        pass


class Entry(BaseWidget):
    """Entry Widget"""
    CODE = 1
    NAME = 'Entry'
    PARENT = 0


class Databases(BaseWidget):
    """Databases Widget"""
    CODE = 2
    NAME = 'Databases'
    PARENT = Entry.CODE

    def __init__(self):
        super().__init__()
        self._databases = None

    @property
    def databases(self):
        if self._databases is None:
            self._databases = fn.load_databases()
        return self._databases

    def do(self):
        console.render_databases(self.databases)


class Snaps(BaseWidget):
    """Snaps Widget"""
    CODE = 3
    NAME = 'Snaps'
    PARENT = Entry.CODE

    def do(self):
        snaps = mem.get('snaps')
        if snaps is None:
            snaps = fn.load_snaps()
            mem.set('snaps', snaps)
        console.render_snaps(snaps)


class Tables(BaseWidget):
    """Database Tables Widget"""
    CODE = 4
    NAME = 'Tables'
    PARENT = Databases.CODE

    def __init__(self):
        super().__init__()
        self.current_database = None

    def do(self):
        database = self.parent.databases[int(input('Database: '))]
        self.current_database = database
        console.render_tables(database.tables())


class CreateSnap(BaseWidget):
    """Create Snap Widget"""
    CODE = 5
    NAME = 'CreateSnap'
    PARENT = Databases.CODE

    def do(self):
        # find database
        database = self.parent.databases[int(input('Database: '))]
        # create snap
        snap = Snap.from_database(database)
        console.success('Snap created successfully')
        # save created snap into snaps directory as pickle
        snap.to_pickle(settings.SNAP_DIR)
        console.success('Snap saved successfully')
        # clear cached snaps
        mem.delete('snaps')


class Compare(BaseWidget):
    """Database Compare Widget"""
    CODE = 6
    NAME = 'Compare'
    PARENT = Snaps.CODE

    def do(self):
        # get snaps
        snaps = mem.get('snaps', [])
        snap1 = snaps[int(input('Snap1: '))]
        snap2 = snaps[int(input('Snap2: '))]
        # compare

        deleted = snap1.difference(snap2)
        new = snap1.r_difference(snap2)
        changed = snap1.changed(snap2)

        mem.set("table_changed", changed[0])
        mem.set("all_changes", changed[1])

        # generate report
        if not any([deleted, new, changed[0]]):
            console.print('No changes detected')
        else:
            console.render_compare(new, deleted, changed[0])


class DeleteSnaps(BaseWidget):
    """Delete All snap in a snaps folder"""
    CODE = 11
    NAME = 'Delete Snaps'
    PARENT = Snaps.CODE

    def do(self):
        user_input = input('Are sure you want to delete all snaps? ([y], n) ').strip().lower()

        if user_input == '' or user_input == 'y':
            try:
                self.delete_snaps(settings.SNAP_DIR)
            except Exception as e:
                console.error(f'Error: {e}')
            else:
                console.success('Deleted all snaps')
                mem.set('snaps', None)
        else:
            console.error('Operation canceled')

    @staticmethod
    def delete_snaps(directory):
        # get listdir from snap folder
        folder_items = os.listdir(directory)
        for item in folder_items:
            if os.path.isdir(item):
                shutil.rmtree(os.path.join(directory, item))


class Columns(BaseWidget):
    """Table Columns Widget"""
    CODE = 7
    NAME = 'Columns'
    PARENT = Tables.CODE

    def do(self):
        table = self.parent.current_database.tables()[int(input('Table: '))]
        columns = self.parent.current_database.columns(table)
        console.render_columns(columns)


class Records(BaseWidget):
    """Table Records Widget"""
    CODE = 8
    NAME = 'Records'
    PARENT = Tables.CODE

    def do(self):
        table = self.parent.current_database.tables()[int(input('Table: '))]
        columns = self.parent.current_database.columns(table)
        records = self.parent.current_database.records(table)
        console.render_records(columns, records)

class ChangedTables(BaseWidget):
    """Changed Columns in a Table"""
    CODE = 9
    NAME = 'View column changes in aTable'
    PARENT = Compare.CODE

    def do(self):
        
        changed_tables = mem.get('table_changed',[])
        selected_tbl = list(changed_tables.keys())[int(input('Table: '))]
        a = console.render_changedColumns(changed_tables,selected_tbl)

        mem.set('selected_tbl', selected_tbl)
        mem.set('selected_clmn', a)
        
        

class ChangedColumns(BaseWidget):
    """Detailed changes in Columns"""
    CODE = 10
    NAME = "View Changes in a Column"
    PARENT = ChangedTables.CODE

    def do (self):
        df = pandas.DataFrame()

        #dataframe containing all changes
        changed_row = mem.get('all_changes')

        selected_table = mem.get('selected_tbl')
        selected_column = mem.get('selected_clmn')

        #obtaining cropped dataframe of changes for selected table
        for j in (i for i in changed_row if selected_table in list(i.keys())):
            df = j.get(selected_table)

        #user selection
        selection = int(input('Column: '))

        #obtaining a cropped dataframe for the selected column
        for j in (i for i in selected_column if selection in i.keys()):
            value = j.get(selection)


        #replacing null values (values that haven't been changed or have benn deleted)       
        user_selection = df.loc[:,value ].fillna(">>??<<")
        
        console.render_changedTable(value, user_selection)

        df.iloc[0:0]

# initialize widgets and set relations
WIDGETS = {
    cls.CODE: cls()
    for cls in BaseWidget.__subclasses__()
}

for widget in WIDGETS.values():
    parent = WIDGETS.get(widget.PARENT)
    if parent:
        widget.parent = parent
        parent.add_child(widget)


# set root
ROOT = WIDGETS.get(1)
