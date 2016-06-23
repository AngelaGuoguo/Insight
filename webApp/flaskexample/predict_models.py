"""
Predict patient risk
"""

import numpy as np
import sklearn
import pandas as pd
from sklearn.preprocessing import normalize
from sklearn import linear_model
import get_features
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve, auc
import pickle
from sklearn import metrics
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.metrics import accuracy_score


def ranked_list(limit=10, reverse=False, p_list=None):
    # first retrieve all patient features
    patients, x = get_features.generate_features()
    patients = np.asmatrix(patients).T

    # even with small number of patients, they should be
    # normalized same ways as all patients
    x_mean = x.mean(axis=0)
    x_std = x.std(axis=0)

    # if a list is provided, re-generated x
    if p_list is not None:
        patients, x = get_features.generate_features(p_list)
        patients = np.asmatrix(patients).T

    # if no qualifying vector is returned, e.g. provided list
    # contains no existing patient, return early with None
    if x is None or x.size == 0:
        return None

    # normalize features
    x_normed = (x - x_mean)/x_std

    # load model
    with open("model.output", "rb") as input_file:
        est = pickle.load(input_file)

    # predict !!
    result = est.predict_proba(x_normed)

    patient_results = np.concatenate((result, patients), axis=1)

    sorted_by_risk = pd.DataFrame(
        patient_results,
        columns=['ready', 'return', 'pid']).sort_values(
            by=['ready'], ascending=False)
    print sorted_by_risk

    # following is sanity check. AUC = AUC I got before => answer is yes
    '''
    Y=pd.read_csv("Y.csv",header=None)
    y = np.asarray(Y)

    false_positive_rate, true_positive_rate, thresholds = \
    roc_curve(y, est.predict(x_normed))

    print auc(false_positive_rate, true_positive_rate)
    roc_auc = auc(false_positive_rate, true_positive_rate)
    print roc_auc_score(y, est.predict(x_normed))
    '''
    # rank by prediction
    # if a patient list is provided, ignore the limit argument
    if reverse:
        if p_list is None:
            tmp = sorted_by_risk.tail(limit).values.tolist()
            tmp.reverse()
            return tmp
        else:
            tmp = sorted_by_risk.values.tolist()
            tmp.reverse()
            print tmp
            return tmp
    else:
        if p_list is None:
            return sorted_by_risk.head(limit).values.tolist()
        else:
            return sorted_by_risk.values.tolist()


def main():
    # simple test, sanity check
    ranked = ranked_list(5)
    print ranked


if __name__ == "__main__":
    main()
