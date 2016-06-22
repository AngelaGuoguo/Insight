# Insight
Insight Data Science Project: Good Heart. Predict readmission risk of ICU patients with cardiovascular conditions

# How it works

Data source: https://mimic.physionet.org/

Postgres code: https://github.com/MIT-LCP/mimic-code, modified as required. Mostly just to get sapsII scores etc for the last day at ICU

Uncomment/comment code as needed

0. util.py contains a list of helper functions. terminal.txt contains several linux commands for file processing you might need.
1. Run python generate_lists.py to generate list of patients with cardiovascular conditions
2. Run features.py to derive various features
3. Use jupyter to modify models.ipynb and try out various machine learning models

Note: notes_nlp.py is half-completed. You can use it to get a prototype LDA model, but I didn't have time to go further and create feature vectors for patients


