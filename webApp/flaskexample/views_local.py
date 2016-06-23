from flaskexample import app
from flask import render_template, jsonify
from flask import request, Flask, url_for
import pickle
import getinfo
import predict_models
import codecs,json
#from wtforms import TextField, Form, TextAreaField, StringField

#app=Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

# retrieve model
with open("model.output", "rb") as input_file:
    model = pickle.load(input_file)

@app.route('/predict/', methods=['POST'])
def predict():
    limit=request.form['pid']
    try:
        num=int(limit)
    except ValueError:
        return render_template('invalid.html',message=\
          "Please enter an integer")
    if num <= 0:
        return render_template('invalid.html',message=\
            "Please enter a positive integer")
    rev=False
    if request.form['Submit']=='Most risk':
        rev=True
    patient_list = predict_models.ranked_list(limit=num,reverse=rev)
    if patient_list == None or len(patient_list)==0:
        return render_template('invalid.html',message=\
            "No patient is in the provided list")
    return render_template('output.html',plist=patient_list)

@app.route('/predict_list/', methods=['POST'])
def predict_list():
    pids=request.form.get('pids')
    lists=pids.split(",")
    int_list=[]
    for w in lists:
        try:
            int_list.append(int(w))
        except ValueError:
            return render_template('invalid.html',message=\
              "Please enter a list of integers, separated by comma and nothing else")
    rev=False
    if request.form['Submit']=='Most risk':
        rev=True
    patient_list = predict_models.ranked_list(limit=0,reverse=rev,p_list=int_list)
    #print int_list
    if patient_list == None or len(patient_list)==0:
        return render_template('invalid.html',message=\
            "No patient is in the provided list")
    return render_template('output.html',plist=patient_list)

@app.route('/_details')
def details():
    pid=request.args.get('id',-2,type=int)
    info=getinfo.get_patient_info(pid)
    info2=getinfo.get_patient_scores(pid)
    return jsonify(result=info,result2=info2)
    
