"""
Retrive patient information from database
"""


import psycopg2
import pandas as pd
import numpy as np
from util import get_sql
from util import load


# obtain patient information for one patient id
def get_patient_info(pid):
    # initialize postgres connection
    con = psycopg2.connect(database='mimic',
                           user='mimic', host='localhost',
                           password='mimic')
    # retrive comorbidity scores
    sql_query = """
    SELECT *
    FROM elixhauser_ahrq
    WHERE SUBJECT_ID = %d
    ;
    """ % (pid)
    comorb = pd.read_sql_query(sql_query, con)

    # limit to first admission
    hadms = load("lists/adults_heart_discharged.csv",
                 cols=['hadm_id'])['hadm_id'].tolist()
    comorb = comorb[comorb['hadm_id'].isin(hadms)]

    # only display comorbidity = 1 items
    positives = comorb.loc[:, (comorb != 0).any(axis=0)]
    col_names = positives.drop(['subject_id', 'hadm_id'],
                               axis=1).columns.values
    return str(col_names.tolist())[1:-1]


# get numerical scores
def get_patient_scores(pid):
    # initialize postgres connection
    con = psycopg2.connect(database='mimic',
                           user='mimic', host='localhost',
                           password='mimic')
    stay_ids = load("lists/adults_heart_discharged.csv",
                    cols=['icustay_id'])['icustay_id'].tolist()

    # retrive from database all relevant scores
    sql_query = """
    SELECT * FROM mimiciii.oasis
    WHERE SUBJECT_ID = %d
    ;
    """ % (pid)
    oasis = pd.read_sql_query(sql_query, con)
    oasis = oasis[oasis['icustay_id'].isin(stay_ids)]

    sql_query = """
    SELECT * FROM mimiciii.sofa
    WHERE SUBJECT_ID = %d
    ;
    """ % (pid)
    sofa = pd.read_sql_query(sql_query, con)
    oasis = oasis[oasis['icustay_id'].isin(stay_ids)]

    sql_query = """
    SELECT * FROM mimiciii.sapsii
    WHERE SUBJECT_ID = %d
    ;
    """ % (pid)
    sapsii = pd.read_sql_query(sql_query, con)
    sapsii = sapsii[sapsii['icustay_id'].isin(stay_ids)]

    sql_query = """
    SELECT * FROM mimiciii.sapsii_last
    WHERE SUBJECT_ID = %d
    ;
    """ % (pid)
    sapsii_last = pd.read_sql_query(sql_query, con)
    sapsii_last = sapsii_last[sapsii_last['icustay_id'].isin(stay_ids)]

    # combine all scores
    data = [oasis.iloc[0][2], sofa.iloc[0][2],
            sapsii.iloc[0][2], sapsii_last.iloc[0][2]]

    # TODO: make a plot and display in html
    '''
    #barplot=ax.bar([0,1,2,3],data,0.6,color=['grey','white','grey','white'])
    #names = ax.set_xticklabels(['severity illness score',
    #                            'organ failure assessment',
    #                            'acute physiology score',
    #                            'acute physiology score(last)'])
    #ax.set_xticks([0,1,2,3])
    #ax.set_xlim(-0.3,3.8)
    #plt.gcf().subplots_adjust(bottom=0.25)
    #plt.setp(names,rotation=30,fontsize=13)
    #savefig("predict/fig.png")
    '''
    return str(data)[1:-1]


def main():
    print get_patient_scores(98887)


if __name__ == '__main__':
    main()
