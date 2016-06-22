import psycopg2
import pandas as pd
import sklearn
from util import load, load_sql
import numpy as np

def comorb_scores(con, hids):
    # extract elixhauser scores
    elix=load_sql(con,'*','elixhauser_ahrq')
    elix=elix[elix['hadm_id'].isin(hids)]
    elix=elix.drop('hadm_id',axis=1).sort_values(by=['subject_id'])
    elix=elix.drop('subject_id',axis=1)
    return elix

def generate_phys_scores(con,icu_list,p_list):
    oasis = load_sql(con,"subject_id,icustay_id, oasis","mimiciii.oasis")
    oasis=oasis[oasis['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])

    oasis_last = load_sql(con,"subject_id,icustay_id, oasis","mimiciii.oasis_last")
    oasis_last=oasis_last[oasis_last['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])

    saps = load_sql(con,'subject_id,icustay_id, saps','mimiciii.saps')
    saps=saps[saps['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])

    sapsii = load_sql(con,'subject_id,icustay_id, sapsii','mimiciii.sapsii')
    sapsii=sapsii[sapsii['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])

    sapsii_last = load_sql(con,'subject_id,icustay_id, sapsii','mimiciii.sapsii_last')
    sapsii_last=sapsii_last[sapsii_last['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])
    
    sofa = load_sql(con,'subject_id,icustay_id, sofa','mimiciii.sofa')
    sofa=sofa[sofa['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])

    icu_los = load_sql(con,'subject_id,icustay_id, los','mimiciii.ICUSTAYS')
    icu_los=icu_los[icu_los['icustay_id'].isin(icu_list)].sort_values(by=['subject_id'])
    
    # turn everything in to matrices
    oasis_m=np.asmatrix(oasis)[:,2]
    oasis_last_m=np.asmatrix(oasis_last)[:,2]
    sofa_m=np.asmatrix(sofa)[:,2]
    saps_m=np.asmatrix(saps)[:,2]
    sapsii_m=np.asmatrix(sapsii)[:,2]
    sapsii_last_m=np.asmatrix(sapsii_last)[:,2]
    icu_los_m=np.asmatrix(icu_los)[:,2]

    age=load("lists/adults_admitted.csv",cols=['subject_id','age'])
    age=age[age['subject_id'].isin(p_list)].sort_values(by=['subject_id'])
    age_m=np.asmatrix(age)[:,1]

    #combine all features into one feature vector
    v=np.concatenate((oasis_m,sofa_m,sapsii_m,sapsii_last_m,age_m,icu_los_m),axis=1)
    return v

def generate_features(provided_list=None):
    con = psycopg2.connect(database = 'mimic', user = 'mimic', host='localhost'\
        , password='mimic')
    # load list of first ham id
    
    first_icu=load("lists/adults_heart_discharged.csv",cols=['subject_id','hadm_id','icustay_id']).sort_values(by=['subject_id'])
    
    # if a patient list if provided, then only look at those patients
    if provided_list != None:
        first_icu=first_icu[first_icu['subject_id'].isin(provided_list)]
    
    hids=set(first_icu['hadm_id'].tolist())          
    icu_list=first_icu['icustay_id'].tolist()
    p_list=first_icu['subject_id'].tolist()
    patients = first_icu['subject_id']
    
    # get comorbidity scores
    comorb = comorb_scores(con,hids)
    
    # get oasis scores etc
    phys_scores = generate_phys_scores(con,icu_list,p_list)
    combined_scores=np.concatenate((np.asmatrix(comorb),phys_scores),axis=1)
    np.savetxt("X.csv", combined_scores, delimiter=",")
    
    return patients, combined_scores

# label positives and negatives based on day threshold
# limit = number of days before readmission
def generate_labels(limit=30):
    patients=load("lists/adults_heart_discharged.csv",cols=['subject_id'])
    cases=load("lists/readmission_diff.csv",cols=['subject_id','diff'])\
        .sort_values(by=['subject_id'])

    labels=pd.merge(cases,patients,on='subject_id',how='right')\
        .sort_values(by=['subject_id'])
    # generate labels
    def labeling(x):
            if x == None:
                return 0
            elif x<limit:
                return 1
            else:
                return 0
    
    labels['label']=labels['diff'].apply(labeling)
    labels['label'].to_csv("Y.csv",header=False,index=False)

    return labels

def main():    
    patients, scores = generate_features()
    labels=generate_labels()
    
if __name__ == "__main__":
    main()
