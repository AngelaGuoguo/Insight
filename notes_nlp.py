"""
!!! INCOMPLETE !!!
Though I completed the most hardware consuming step: lda,
I decided to stop here and didn't continue feature generation
and such, for the sake of ROI
"""

import psycopg2
import pandas as pd
import util
from util import load
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer
import math
import gensim
from gensim import corpora, models


# retrive notes from postseq
def retrieve_notes_sql():
    con = psycopg2.connect(database='mimic', user='mimic', host='localhost',
                           password='mimic')

    # load list of first icus
    icu_list = load("notes/adults_heart_discharged.csv",
                    cols=['subject_id', 'hadm_id'])

    adm_id = icu_list['hadm_id'].tolist()

    # then find the first icu stay not in above list
    query_list = "("+str(adm_id)[1:-1]+")"

    # get all relevant note during first stay
    sql_query = """
        SELECT SUBJECT_ID,hadm_id, chartdate, charttime,text
        FROM mimiciii.noteevents
        WHERE (hadm_id IN %s AND category != 'Discharge summary')
        ORDER BY SUBJECT_ID, chartdate, charttime
        ;
        """ % query_list
    notes = pd.read_sql_query(sql_query, con)
    notes.to_csv("notes/notes.csv", index=False)
    # print notes.shape
    return True


# start reference: http://stevenloria.com/finding-important-
# words-in-a-document-using-tf-idf/
def tf(word, doc):
    if len(doc) == 0:
        return 0
    return float(doc.count(word)) / len(doc)


def df(word, docs):
    return sum(1 for doc in docs if word in doc)


# drop the log term. No need for LDA. add 1 to denominater
# to avoid infinity
def idf(word, docs):
    return float(len(docs)) / (1 + df(word, docs))
# print idf('a',docs),idf('b',docs)


def tfidf(word, doc, docs):
    return tf(word, doc) * idf(word, docs)
# end reference


def tokenize_notes(text):
    tokenizer = RegexpTokenizer(r'\w+')
    raw = text.lower()
    tokens = tokenizer.tokenize(raw)
    # stop words
    stop = get_stop_words('en')
    stopped = [i for i in tokens if i not in stop]
    # stemmer: No! stemmer is a bad choice for doc notes
    # stemmer = PorterStemmer()
    # stemed = [stemmer.stem(i) for i in stopped]
    return stopped


def tokenize_file(path_in, path_out):
    f_out = open(path_out, 'w')
    counter = 0

    with open(path_in, 'r') as f:
        for line in f:
            if counter % 10000 == 0:
                print counter
            counter += 1
            s = line.split(",")
            words = tokenize_notes(s[5])
            for word in words:
                f_out.write(str(word)+" ")
            f_out.write('\n')
    f_out.close()
    f.close()
    return 0

# I really need to trim down the texts to do lda
# main issue: such a big dictionary wont fit into
# the memory. I'll do it the naive stream way

# OK, let's just get rid of some samples for efficiency...
#


# well, try lda first anyways
def generate_top_words(path_in, path_out, limit=500):
    # get collection of docs from path_in
    f_out = open(path_out, 'w')
    docs = []

    counter = 0
    with open(path_in, 'r') as f:
        for line in f:
            if counter % 10000 == 0:
                print counter
            counter += 1
            s = line[:-2].split(' ')
            docs.append(s)
    f.close()
    # ref: https://rstudio-pubs-static.s3.amazonaws.com/
    # 79360_850b2a69980c4488b1db95987a24867a.html
    dictionary = corpora.Dictionary(docs)
    corpus = [dictionary.doc2bow(text) for text in docs]
    ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=20,
                                               id2word=dictionary)
    ldamodel.save("notes/ldamodel_all")
    topics = ldamodel.show_topics(num_topics=20, num_words=20)
    for topic in topics:
        f_out.write(str(topic))
        f_out.write('\n')
    f_out.close()
    return 0


def build_dict_tokens(path_in, path_out):
    # get a set
    counter = 0
    unique = set()
    with open(path_in, 'r') as f:
        for line in f:
            if counter % 10000 == 0:
                print counter
                print unique
            counter += 1
            words = line.split(' ')
            for w in words:
                unique.add(w)
    f.close()
    zipped = zip(unique, range(len(unique)))
    with open(path_out, 'w') as fout:
        fout.write('word,indx\n')
        for x, y in zipped:
            string = x+','+str(y)+'\n'
            fout.write(string)
    fout.close()


def main():
    # retrieve_notes_sql()
    # tokenize_file("notes/notes_single_line.csv",'notes/tokenized_all.txt',)
    # then sed '1d' file_out > tmp; mv tmp file_out to remove first header line

    # I probably should turn words into ints for efficiency
    # build_dict_tokens('notes/tokenized_all.txt','notes/unique_words.txt')

    # generate top words
    generate_top_words('notes/tokenized_all.txt',
                       'notes/top_words_all_notes.txt')
    return 0


if __name__ == "__main__":
    main()
