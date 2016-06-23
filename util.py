"""
A bunch of helper functions
"""

from datetime import datetime
import pandas as pd
import numpy as np
import string


# load postgres database
def load_sql(con, select, db):
    sql_query = """
    SELECT %s
    FROM %s
    ;
    """ % (select, db)
    return pd.read_sql_query(sql_query, con)


# convert string to time using specific format
def convert_time(x):
    if type(x) != str:
        print "Invalid ", x
    return datetime.strptime(x, '%Y-%m-%d %H:%M:%S')


# loading csv
def load(path, h=1, cols=None, ddtype=None):
    if h == 0:
        return pd.read_csv(path, header=None, usecols=cols, dtype=ddtype)
    return pd.read_csv(path, usecols=cols, dtype=ddtype)


# returns whether input s has any string in it
def hasString(s):
    letters = [i for i in string.lowercase[:26]+string.uppercase[:26]]
    symbols = [i for i in '{}()\%[],:;+-*/&|<>=~']
    remove = letters+symbols

    tag = False
    if type(s[0]) == float:
        return False
    else:
        if s[0] == '.':
            return True
        for i in s[0]:
            if i in remove or i == "\'" or i == ",":
                return True
    return False


# method name not precise, it returns true as long as s is not a number
# Not necessarily a string
def isString(s):
    try:
        tmp = float(s)
    except ValueError, e:
        return True
    return False


# hunts down which csv row contains a string
def findString(path, col=0, start=1):
    f = open(path, 'r').readlines()
    N = len(f)-1
    print "checking %d lines" % (N)
    # skip header by default (start=1)
    for i in range(start, N):
        w = f[i].split(",")
        try:
            tmp = float(w[col])
        except ValueError, e:
            print "error", e, f[i], " on line", i
            return True
    return False


# Given list of all subjects and list of cases
# return separated lists of total, contrl, and case
def patient_lists(name_path, case_path):
    print "loading patient lists..."
    all_pd = load(name_path, h=0)
    case_pd = load(case_path)

    all_id = set(all_pd[0].tolist())
    case_id = set(case_pd['subject_id'].tolist())
    ctrl_id = all_id-case_id
    print "control: %d; case: %d" % (len(ctrl_id), len(case_id))
    return all_id, ctrl_id, case_id
