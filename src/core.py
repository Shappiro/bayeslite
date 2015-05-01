# -*- coding: utf-8 -*-

#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Miscellaneous utilities for managing BayesDB entities.

Tables, generators, and columns are named with strs.  Only US-ASCII is
allowed, no Unicode.

Each table has a nonempty sequence of named columns.  As in sqlite3,
tables may be renamed and do not necessarily have numeric ids, so
there is no way to have a handle on a table that is persistent outside
a savepoint.

Each table may optionally be modelled by any number of generators,
representing a parametrized generative model for the table's data,
according to a named metamodel.  For each table, at most one generator
may be designated as the default generator for the table.

Each generator models a subset of the columns in its table, which are
called the modelled columns of that generator.  Each column in a
generator has an associated statistical type.  Like tables, generators
may be renamed.  Unlike tables, each generator has a numeric id, which
is never reused and therefore persistent across savepoints.

Each generator may have any number of different models, each
representing a particular choice of parameters for the parametrized
generative model.  Models are numbered consecutively for the
generator, and may be identified uniquely by ``(generator_id,
modelno)`` or ``(generator_name, modelno)``.

Tables and generators may not share names.  In most contexts, where a
generator's name is needed, the name of a table with a default
generator may be substituted.

"""

from bayeslite.sqlite3_util import sqlite3_quote_name

def bayesdb_has_table(bdb, name):
    """True if there is a table named `name` in `bdb`.

    The table need not be modelled.
    """
    qt = sqlite3_quote_name(name)
    cursor = bdb.sql_execute('PRAGMA table_info(%s)' % (qt,))
    try:
        cursor.next()
    except StopIteration:
        return False
    else:
        return True

def bayesdb_table_column_names(bdb, table):
    """Return a list of names of columns in the table named `table`.

    The results strs and are ordered by column number.

    `bdb` must have a table named `table`.  If you're not sure, call
    :func:`bayesdb_has_table` first.
    """
    if not bayesdb_has_table(bdb, table):
        raise ValueError('No such table: %s' % (repr(table),))
    sql = '''
        SELECT name FROM bayesdb_column WHERE tabname = ?
            ORDER BY colno ASC
    '''
    # str because column names can't contain Unicode in sqlite3.
    return [str(row[0]) for row in bdb.sql_execute(sql, (table,))]

def bayesdb_table_column_name(bdb, table, colno):
    """Return the name of the column numbered `colno` in `table`.

    `bdb` must have a table named `table`.  If you're not sure, call
    :func:`bayesdb_has_table` first.
    """
    sql = '''
        SELECT name FROM bayesdb_column WHERE tabname = ? AND colno = ?
    '''
    cursor = bdb.sql_execute(sql, (table, colno))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such column number in table %s: %d' %
            (repr(table), colno))
    else:
        return row[0]

def bayesdb_table_column_number(bdb, table, name):
    """Return the number of column named `name` in `table`.

    `bdb` must have a table named `table`.  If you're not sure, call
    :func:`bayesdb_has_table` first.
    """
    sql = '''
        SELECT colno FROM bayesdb_column WHERE tabname = ? AND name = ?
    '''
    cursor = bdb.sql_execute(sql, (table, name))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such column in table %s: %s' %
            (repr(table), repr(name)))
    else:
        return row[0]

def bayesdb_table_guarantee_columns(bdb, table):
    """Make sure ``bayesdb_column`` is populated with columns of `table`.

    `bdb` must have a table named `table`.  If you're not sure, call
    :func:`bayesdb_has_table` first.
    """
    with bdb.savepoint():
        qt = sqlite3_quote_name(table)
        insert_column_sql = '''
            INSERT OR IGNORE INTO bayesdb_column (tabname, colno, name)
                VALUES (?, ?, ?)
        '''
        nrows = 0
        for row in bdb.sql_execute('PRAGMA table_info(%s)' % (qt,)):
            nrows += 1
            colno, name, _sqltype, _notnull, _default, _primary_key = row
            bdb.sql_execute(insert_column_sql, (table, colno, name))
        if nrows == 0:
            raise ValueError('No such table: %s' % (repr(table),))

def bayesdb_table_has_column(bdb, table, name):
    """True if the table named `table` has a column named `name`.

    `bdb` must have a table named `table`.  If you're not sure, call
    :func:`bayesdb_has_table` first.
    """
    sql = 'SELECT COUNT(*) FROM bayesdb_column WHERE tabname = ? AND name = ?'
    cursor = bdb.sql_execute(sql, (table, name))
    return cursor.next()[0]

def bayesdb_has_generator(bdb, name):
    """True if there is a generator named `name` in `bdb`.

    Only actual generator names are considered.
    """
    sql = 'SELECT COUNT(*) FROM bayesdb_generator WHERE name = ?'
    cursor = bdb.sql_execute(sql, (name,))
    return cursor.next()[0] != 0

def bayesdb_has_generator_default(bdb, name):
    """True if there is a generator or default-modelled table named `name`."""
    sql = '''
        SELECT COUNT(*) FROM bayesdb_generator
            WHERE name = :name OR (defaultp AND tabname = :name)
    '''
    cursor = bdb.sql_execute(sql, {'name': name})
    return cursor.next()[0] != 0

def bayesdb_get_generator(bdb, name):
    """Return the id of the generator named `name` in `bdb`.

    The id is persistent across savepoints: ids are 64-bit integers
    that increase monotonically and are never reused.

    `bdb` must have a generator named `name`.  If you're not sure,
    call :func:`bayesdb_has_generator` first.
    """
    sql = 'SELECT id FROM bayesdb_generator WHERE name = ?'
    cursor = bdb.sql_execute(sql, (name,))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such generator: %s' % (repr(name),))
    else:
        assert isinstance(row[0], int)
        return row[0]

def bayesdb_get_generator_default(bdb, name):
    """Return the id of the (default) generator named `name` in `bdb`.

    The id is persistent across savepoints: ids are 64-bit integers
    that increase monotonically and are never reused.

    `bdb` must have a generator named `name`, or a modelled table
    named `name` with a default generator.  If you're not sure, call
    :func:`bayesdb_has_generator_default` first.
    """
    sql = '''
        SELECT id FROM bayesdb_generator
            WHERE name = :name OR (defaultp AND tabname = :name)
    '''
    cursor = bdb.sql_execute(sql, {'name': name})
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such generator: %s' % (repr(name),))
    else:
        assert isinstance(row[0], int)
        return row[0]

def bayesdb_generator_name(bdb, id):
    """Return the name of the generator with id `id`."""
    sql = 'SELECT name FROM bayesdb_generator WHERE id = ?'
    cursor = bdb.sql_execute(sql, (id,))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such generator id: %d' % (repr(id),))
    else:
        return row[0]

def bayesdb_generator_metamodel(bdb, id):
    """Return the name of the metamodel of the generator with id `id`."""
    sql = 'SELECT metamodel FROM bayesdb_generator WHERE id = ?'
    cursor = bdb.sql_execute(sql, (id,))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such generator: %s' % (repr(id),))
    else:
        if row[0] not in bdb.metamodels:
            name = bayesdb_generator_name(bdb, id)
            raise ValueError('Metamodel of generator %s not registered: %s' %
                (repr(name), repr(row[0])))
        return bdb.metamodels[row[0]]

def bayesdb_generator_table(bdb, id):
    """Return the name of the table of the generator with id `id'."""
    sql = 'SELECT tabname FROM bayesdb_generator WHERE id = ?'
    cursor = bdb.sql_execute(sql, (id,))
    try:
        row = cursor.next()
    except StopIteration:
        raise ValueError('No such generator: %s' % (repr(id),))
    else:
        assert len(row) == 1
        return row[0]

def bayesdb_generator_column_names(bdb, generator_id):
    """Return a list of names of columns modelled by `generator_id`."""
    sql = '''
        SELECT c.name
            FROM bayesdb_column AS c,
                bayesdb_generator AS g,
                bayesdb_generator_column AS gc
            WHERE g.id = ?
                AND gc.generator_id = g.id
                AND c.tabname = g.tabname
                AND c.colno = gc.colno
            ORDER BY c.colno ASC
    '''
    # str because column names can't contain Unicode in sqlite3.
    return [str(row[0]) for row in bdb.sql_execute(sql, (generator_id,))]

def bayesdb_generator_column_stattype(bdb, generator_id, colno):
    """Return the statistical type of the column `colno` in `generator_id`."""
    sql = '''
        SELECT stattype FROM bayesdb_generator_column
            WHERE generator_id = ? AND colno = ?
    '''
    cursor = bdb.sql_execute(sql, (generator_id, colno))
    try:
        row = cursor.next()
    except StopIteration:
        generator = bayesdb_generator_name(bdb, generator_id)
        sql = '''
            SELECT COUNT(*)
                FROM bayesdb_generator AS g, bayesdb_column AS c
                WHERE g.id = :generator_id
                    AND g.tabname = c.tabname
                    AND c.colno = :colno
        '''
        cursor = bdb.sql_execute(sql, {
            'generator_id': generator_id,
            'colno': colno,
        })
        if cursor.next()[0] == 0:
            raise ValueError('No such column in generator %s: %d' %
                (generator, colno))
        else:
            raise ValueError('Column not modelled in generator %s: %d' %
                (generator, colno))
    else:
        assert len(row) == 1
        return row[0]

def bayesdb_generator_column_name(bdb, generator_id, colno):
    """Return the name of the column numbered `colno` in `generator_id`."""
    sql = '''
        SELECT c.name
            FROM bayesdb_generator AS g,
                bayesdb_generator_column AS gc,
                bayesdb_column AS c
            WHERE g.id = :generator_id
                AND gc.colno = :colno
                AND g.id = gc.generator_id
                AND g.tabname = c.tabname
                AND gc.colno = c.colno
    '''
    cursor = bdb.sql_execute(sql, {
        'generator_id': generator_id,
        'colno': colno,
    })
    try:
        row = cursor.next()
    except StopIteration:
        generator = bayesdb_generator_name(bdb, generator_id)
        raise ValueError('No such column number in generator %s: %d' %
            (repr(generator), colno))
    else:
        assert len(row) == 1
        return row[0]

def bayesdb_generator_column_number(bdb, generator_id, column_name):
    """Return the number of the column `column_name` in `generator_id`."""
    sql = '''
        SELECT c.colno
            FROM bayesdb_generator AS g,
                bayesdb_generator_column as gc,
                bayesdb_column AS c
            WHERE g.id = :generator_id AND c.name = :column_name
                AND g.id = gc.generator_id
                AND g.tabname = c.tabname
                AND gc.colno = c.colno
    '''
    cursor = bdb.sql_execute(sql, {
        'generator_id': generator_id,
        'column_name': column_name,
    })
    try:
        row = cursor.next()
    except StopIteration:
        generator = bayesdb_generator_name(bdb, generator_id)
        raise ValueError('No such column in generator %s: %s' %
            (repr(generator), repr(column_name)))
    else:
        assert len(row) == 1
        assert isinstance(row[0], int)
        return row[0]

def bayesdb_generator_column_numbers(bdb, generator_id):
    """Return a list of the numbers of columns modelled in `generator_id`."""
    sql = '''
        SELECT colno FROM bayesdb_generator_column
            WHERE generator_id = ?
            ORDER BY colno ASC
    '''
    return [row[0] for row in bdb.sql_execute(sql, (generator_id,))]

def bayesdb_generator_has_model(bdb, generator_id, modelno):
    """True if `generator_id` has a model numbered `modelno`."""
    sql = '''
        SELECT COUNT(*) FROM bayesdb_generator_model AS m
            WHERE generator_id = ? AND modelno = ?
    '''
    cursor = bdb.sql_execute(sql, (generator_id, modelno))
    return cursor.next()[0] != 0
