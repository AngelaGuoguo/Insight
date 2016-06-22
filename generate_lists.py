# use this file to generate list of patients for different purposes
# Version II
import psycopg2
import pandas as pd
import util
from util import load, load_sql


# calculate patients' icu visit frequencies
# inputs:
# con: postgres connection
# path_in, path_out: csv containing patient ids, path to save freq
def frequency_counts(con, path_in, path_out):
    patients = pd.read_csv(path_in, usecols=['subject_id'])

    # generate patient list
    p_list = patients['subject_id'].tolist()

    # request icu events
    icu = load_sql(con, "SUBJECT_ID,INTIME,OUTTIME,LOS",
                   "mimiciii.ICUSTAYS")

    # only keep relevant patients
    icu = icu[icu['subject_id'].isin(p_list)]

    # assign icu frequencies to patients
    icu_counts = icu['subject_id'].value_counts().to_frame()
    icu_counts['id'] = icu_counts.index
    icu_counts.columns = ['counts', 'subject_id']

    # save icu frequencites to file
    icu_counts.to_csv(path_out, index=False)

    # return list of patients admitted twice
    twice = icu_counts[icu_counts['counts'] == 2]
    return twice['subject_id'].tolist()


# calculate difference between icu visits
# input: list of patient ids
# output: subject_id, first ICU ID, second ICU ID, diff
def readmission_diff(con, patients):

    # get list of first icu stays
    sql_query = """
    SELECT DISTINCT ON (SUBJECT_ID)
        SUBJECT_ID,ICUSTAY_ID, INTIME, OUTTIME
    FROM mimiciii.ICUSTAYS
    ORDER BY SUBJECT_ID, INTIME
    ;
    """

    first_icu = pd.read_sql_query(sql_query, con)
    first_icu = first_icu[first_icu['subject_id'].
                          isin(patients)].drop(['intime'], axis=1)

    icu_id = first_icu['icustay_id'].tolist()

    # then find the first icu stay not in above list
    # = second icu stay
    query_list = "("+str(icu_id)[1:-1]+")"

    sql_query = """
    SELECT DISTINCT ON (SUBJECT_ID)
        SUBJECT_ID,ICUSTAY_ID, INTIME, OUTTIME
    FROM mimiciii.ICUSTAYS
    WHERE ICUSTAY_ID NOT IN %s
    ORDER BY SUBJECT_ID, INTIME
    ;
    """ % query_list

    second_icu = pd.read_sql_query(sql_query, con)
    second_icu = second_icu[second_icu['subject_id'].
                            isin(patients)].drop(['outtime'], axis=1)

    readmission = pd.merge(first_icu, second_icu, on='subject_id',
                           how='inner').sort_values(by=['subject_id'])

    readmission['diff'] = (readmission['intime']-readmission['outtime']).\
        dt.days
    readmission.columns = ['subject_id', 'first_icu',
                           'first_out', 'second_icu', 'second_in', 'diff']
    return readmission


# return and save the list of all patients that were adults (age>=15)
# at time of first admission and stayed in ICU for at least 24 hours
def extract_adults(con):
    # get list of all patients
    patients = load_sql(con, "SUBJECT_ID, DOB, DOD, DOD_HOSP, DOD_SSN",
                        "mimiciii.patients")
    print 'patients count ', patients.shape[0]

    # consolidate date of death
    def dod(a, b, c):
        if b is not None:
            return b
        elif a is not None:
            return a
        else:
            return c

    patients['combined_dod'] = patients.apply(
                lambda row: dod(row['dod'], row['dod_hosp'],
                                row['dod_ssn']), axis=1)

    # get list of first icu stays
    sql_query = """
    SELECT DISTINCT ON (SUBJECT_ID)
        SUBJECT_ID, INTIME, OUTTIME
    FROM mimiciii.ICUSTAYS
    WHERE LOS >= 1
    ORDER BY SUBJECT_ID, INTIME
    ;
    """
    first_icu = pd.read_sql_query(sql_query, con)
    print "first icu stayed >= 24 hours", first_icu.shape[0]

    icu_patients = pd.merge(patients, first_icu, on=u'subject_id', how='inner')
    icu_patients['age'] = (icu_patients[u'intime'] -
                           icu_patients[u'dob']).dt.days/365

    # relax adults to age >=15
    adults = icu_patients[icu_patients['age'] >= 15]

    print "adults admitted and stayed for >= 24 hrs: ", adults.shape[0]
    return adults


# input: 'patients' should be a dataframe with dod and discharge time
def lived(patients):
    # discharged alive
    # = patients still lived + patients died >=1 day after discharged
    still_lived = patients[patients['combined_dod'].isnull()]

    dead = patients[~patients['combined_dod'].isnull()].copy()
    dead['dod'] = dead['combined_dod'].apply(util.convert_time)
    dead = dead[~dead['outtime'].isnull()]
    dead['outtime'] = dead['outtime'].apply(util.convert_time)
    dead['lived'] = (dead['dod'] - dead['outtime']).dt.days

    discharged = (dead[dead['lived'] >= 1]).drop(['lived'], axis=1)

    combined = pd.concat([still_lived,
                          discharged]).sort_values(by=['subject_id']).
    drop(['dod', 'combined_dod', 'outtime'], axis=1)

    combined = combined[['subject_id', 'hadm_id', 'icustay_id', 'age']]
    return combined


# input: postgres connection, list of patients to be filtered
def generate_heart_patients(con, patients):
    '''
    will be based on comorbidity label
    1: congestive_heart_failure
    2: cardiac_arrhythmias
    3. valvular_disease
    4. pulmonary_circulation
    5. peripheral_vascular
    6. hypertension
    '''

    # get HADM_ID associated with first icu stay
    # since that's what's used by comorbidity
    sql_query = """
    SELECT DISTINCT ON (SUBJECT_ID)
        SUBJECT_ID, HADM_ID, ICUSTAY_ID
        FROM MIMICIII.ICUSTAYS
        ORDER BY SUBJECT_ID, INTIME
    """
    hadms = pd.read_sql_query(sql_query, con)
    hadms = hadms[hadms['subject_id'].isin(patients)]
    hadms_list = set(hadms['hadm_id'].tolist())

    # from table elixhauser_ahrq
    sql_query = """
    SELECT SUBJECT_ID, HADM_ID
        FROM elixhauser_ahrq
        WHERE (congestive_heart_failure+
            cardiac_arrhythmias + valvular_disease
            + pulmonary_circulation + peripheral_vascular
            + hypertension) >= 1
    ;
    """
    comorbidity = pd.read_sql_query(sql_query, con)

    # narrow down to first icu stays
    comorbidity = comorbidity[comorbidity['hadm_id'].isin(hadms_list)]
    merged = pd.merge(comorbidity, hadms,
                      on=['subject_id', 'hadm_id'], how='inner')
    return merged


# show control vs case numbers. To see class imbalance
def generate_case(path_in, path_out, limit):
    all_df = pd.read_csv(path_in)
    case = all_df[all_df['diff'] <= limit]

    case.to_csv(path_out, index=False)
    print all_df.shape, case.shape


def generate_icu_id(con, names_path, path_out):
    # get list of first icu stays
    sql_query = """
    SELECT DISTINCT ON (SUBJECT_ID)
        SUBJECT_ID, ICUSTAY_ID
    FROM mimiciii.ICUSTAYS
    ORDER BY SUBJECT_ID, INTIME
    ;
    """

    first_icu = pd.read_sql_query(sql_query, con)
    names_df = pd.read_csv(names_path, usecols=['subject_id'])
    name_list = names_df['subject_id'].tolist()
    icu_list = first_icu[first_icu['subject_id'].isin(name_list)]
    icu_list['icustay_id'].to_csv(path_out, index=False, header=False)


def main():
    # establish postgresql connection
    con = psycopg2.connect(database='mimic', user='mimic',
                           host='localhost', password='mimic')

    # 1. extract and export list of adults
    adults = extract_adults(con)
    adults.to_csv("lists/adults_admitted.csv", index=False,
                  columns=['subject_id', 'combined_dod', 'outtime', 'age'])
    # ----

    # 2. extract patients with cardiovascular conditions
    adults = load("lists/adults_admitted.csv")
    adults_list = set(adults['subject_id'].tolist())

    heart_patients = generate_heart_patients(con, adults_list)
    heart_patients.to_csv("lists/heart_patients.csv", index=False, header=True)

    adults_heart = pd.merge(adults, heart_patients,
                            on=['subject_id'], how='inner')

    # 3. then trim down the list to patients who were discharged alive
    discharged = lived(adults_heart)
    discharged.to_csv("lists/adults_heart_discharged.csv", index=False)

    # discharged = load("lists/adults_heart_discharged.csv")

    # 4. from those discharged patients, find the ones with a second
    # admission and calculate the data difference between first and second
    readmitted = readmission_diff(con, discharged['subject_id'].tolist())
    readmitted.to_csv("lists/readmission_diff.csv", index=False)

    # 5. generate icu id's of first visits (could be used for awk)
    generate_icu_id(con, "lists/readmission_diff.csv",
                    "lists/first_icu_list.txt")

    # print "now run: "
    # print "awk -F, 'FNR==NR{k[$1]=1;next;} FNR==1 || k[$4]' list file"
    # change $4 to $[columne number, 1-based] as necessary


if __name__ == '__main__':
    main()
