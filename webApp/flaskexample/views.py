"""
The main routing code that communicates between web page
and python scripts
"""


from flaskexample import app
from flask import render_template, jsonify
from flask import request, Flask, url_for
import pickle
from flaskexample import getinfo, predict_models
import codecs
import json


# index page is also the input page
@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


# contact information
@app.route("/contact")
def contact():
    return render_template("contact.html")


# "about me" page
@app.route("/about")
def about():
    return render_template("about.html")


# page for embedded google slides
@app.route("/slides")
def slides():
    return render_template("slides.html")


# retrieve model
with open("model.output", "rb") as input_file:
    model = pickle.load(input_file)
input_file.close()


# main function: generate risk prediction and ranking
@app.route('/predict/', methods=['POST'])
def predict():
    # limit of how many patients to show
    limit = request.form['pid']
    try:
        num = int(limit)
    except ValueError:
        return render_template('invalid.html',
                               message="Please enter an integer")
    if num <= 0:
        return render_template('invalid.html',
                               message="Please enter a positive integer")

    # since I decided to only show warning, rank by risk is better
    rev = True
    if request.form['Submit'] == 'Rank by risk':
        rev = True

    patient_list = predict_models.ranked_list(limit=num, reverse=rev)
    if patient_list is None or len(patient_list) == 0:
        return render_template('invalid.html',
                               message="No patient is in the provided list")
    return render_template('output.html', plist=patient_list)


# Similar to 'predict', but instead of ranking all patients,
# only rank patients in the provided list
# If more time, should combine these two into one function
@app.route('/predict_list/', methods=['POST'])
def predict_list():
    # retrive the list of patients from input page
    pids = request.form.get('pids')
    lists = pids.split(",")
    int_list = []

    # parse patient list into integers
    for w in lists:
        try:
            int_list.append(int(w))
        except ValueError:
            return render_template('invalid.html',
                                   message="Invalid patient IDs. \
                                   Please enter patient IDs, \
                                   separated by comma. No spaces.")

    # Since I decided to rank risk and never by readyness, set
    # default to "reverse", otherwise should set it to false
    rev = True
    if request.form['Submit'] == 'Rank by risk':
        rev = True
    patient_list = predict_models.ranked_list(limit=0,
                                              reverse=rev,
                                              p_list=int_list)

    if patient_list is None or len(patient_list) == 0:
        return render_template('invalid.html',
                               message="No patient is in the provided list")
    return render_template('output.html', plist=patient_list)


# provide patient details
@app.route('/_details')
def details():
    # Note: since 'id' is generated myself, it's safe to assume
    # integer
    pid = request.args.get('id', -2, type=int)
    info = getinfo.get_patient_info(pid)
    info2 = getinfo.get_patient_scores(pid)
    return jsonify(result=info, result2=info2)


# if __name__ == "__main__":
#    app.run(host='0.0.0.0', port=5000)
