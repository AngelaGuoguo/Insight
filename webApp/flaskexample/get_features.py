"""
Construct feature vectors, given list of patients
In the absence of list, create features for all patients
The output will be an numpy matrix, one row per patient
"""


import psycopg2
import pandas as pd
from util import load, get_sql
import numpy as np


# categorical comorbidiy scores
def comorb_scores(con, hids):
    # extract elixhauser scores
    elix = get_sql(con, '*', 'elixhauser_ahrq')
    elix = elix[elix['hadm_id'].isin(hids)]

    elix = elix.drop('hadm_id', axis=1).sort_values(by=['subject_id'])
    elix = elix.drop('subject_id', axis=1)
    return elix


# numerical physiological scores
def get_phys_scores(con, icu_list, p_list):
    oasis = get_sql(con, "subject_id,icustay_id, oasis", "mimiciii.oasis")
    oasis = oasis[oasis['icustay_id'].isin(icu_list)].sort_values(
        by=['subject_id'])

    oasis_last = get_sql(con,
                         "subject_id,icustay_id, oasis",
                         "mimiciii.oasis_last")
    oasis_last = oasis_last[oasis_last['icustay_id'].
                            isin(icu_list)].sort_values(by=['subject_id'])

    saps = get_sql(con, 'subject_id,icustay_id, saps', 'mimiciii.saps')
    saps = saps[saps['icustay_id'].isin(icu_list)].sort_values(
        by=['subject_id'])

    sapsii = get_sql(con, 'subject_id,icustay_id, sapsii', 'mimiciii.sapsii')
    sapsii = sapsii[sapsii['icustay_id'].
                    isin(icu_list)].sort_values(by=['subject_id'])

    sapsii_last = get_sql(con,
                          'subject_id,icustay_id, sapsii',
                          'mimiciii.sapsii_last')
    sapsii_last = sapsii_last[sapsii_last['icustay_id'].
                              isin(icu_list)].sort_values(by=['subject_id'])

    sofa = get_sql(con, 'subject_id,icustay_id, sofa', 'mimiciii.sofa')
    sofa = sofa[sofa['icustay_id'].isin(icu_list)].\
        sort_values(by=['subject_id'])

    # length of stay as numerical feature
    icu_los = get_sql(con, 'subject_id,icustay_id, los',
                      'mimiciii.ICUSTAYS')
    icu_los = icu_los[icu_los['icustay_id'].isin(
        icu_list)].sort_values(by=['subject_id'])

    # turn everything in to matrices
    oasis_m = np.asmatrix(oasis)[:, 2]
    oasis_last_m = np.asmatrix(oasis_last)[:, 2]
    sofa_m = np.asmatrix(sofa)[:, 2]
    saps_m = np.asmatrix(saps)[:, 2]
    sapsii_m = np.asmatrix(sapsii)[:, 2]
    sapsii_last_m = np.asmatrix(sapsii_last)[:, 2]
    icu_los_m = np.asmatrix(icu_los)[:, 2]

    age = load("lists/adults_admitted.csv",
               cols=['subject_id', 'age'])
    age = age[age['subject_id'].isin(
        p_list)].sort_values(by=['subject_id'])
    age_m = np.asmatrix(age)[:, 1]

    # combine all features into one feature vector and return
    v = np.concatenate((oasis_m, sofa_m, sapsii_m, sapsii_last_m,
                        age_m, icu_los_m), axis=1)
    return v


def generate_features(provided_list=None):
    con = psycopg2.connect(database='mimic', user='mimic',
                           host='localhost', password='mimic')
    # load list of first ham id
    first_icu = load("lists/adults_heart_discharged.csv",
                     cols=['subject_id', 'hadm_id',
                           'icustay_id']).sort_values(by=['subject_id'])

    # if a patient list if provided, then only look at those patients
    if provided_list is not None:
        first_icu = first_icu[first_icu['subject_id'].isin(provided_list)]

    hids = set(first_icu['hadm_id'].tolist())
    icu_list = first_icu['icustay_id'].tolist()
    p_list = first_icu['subject_id'].tolist()
    patients = first_icu['subject_id']

    # get comorbidity scores
    comorb = comorb_scores(con, hids)

    # get oasis scores etc
    phys_scores = get_phys_scores(con, icu_list, p_list)
    combined_scores = np.concatenate((np.asmatrix(comorb),
                                      phys_scores), axis=1)
    # below line is commented out because files with no
    # write-protection should not be used for multi-user
    # application !!
    # np.savetxt("X.csv", combined_scores, delimiter=",")

    return patients, combined_scores


def main():
    patients, scores = generate_features()
    print patients.shape, scores.shape


if __name__ == "__main__":
    main()
