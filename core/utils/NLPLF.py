import numpy as np
import pandas as pd
pd.set_option('display.max_colwidth', -1)
import os, time

import string, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

from scipy.sparse import csr_matrix
import sparse_dot_topn.sparse_dot_topn as ct
from ftfy import fix_text

from snorkel.labeling import LabelingFunction
from snorkel.labeling import LFAnalysis

def ngrams(string, n=3):

    string = fix_text(string) # fix text encoding issues
    string = string.encode("ascii", errors="ignore").decode() #remove non ascii chars
    string = string.lower() #make lower case
    chars_to_remove = [")","(",".","|","[","]","{","}","'"]
    rx = '[' + re.escape(''.join(chars_to_remove)) + ']'
    string = re.sub(rx, '', string) #remove the list of chars defined above
    string = string.replace('&', 'and')
    string = string.replace(',', ' ')
    string = string.replace('-', ' ')
    string = string.title() # normalise case - capital at start of each word
    string = re.sub(' +',' ',string).strip() # get rid of multiple spaces and replace with a single space
    string = ' '+ string +' ' # pad names for ngrams...
    string = re.sub(r'[,-./]|\sBD',r'', string)
    ngrams = zip(*[string[i:] for i in range(n)])
    return [''.join(ngram) for ngram in ngrams]

###matching query:
def getNearestN(query, vectorizer, nbrs):
    queryTFIDF_ = vectorizer.transform(query)
    distances, indices = nbrs.kneighbors(queryTFIDF_)
    return distances, indices

def NLP_matching(tweet_texts, category_keywords, category_names):
    """
    Function: Find the most apropriate category for tweets using their associated keywords/texts

    Input:
        - tweet_texts (list)
        - category_keywords (list / np.array): e.g. ['refund cancel cancelled', 'COVID virus coronavirus']
        - category_names (list): e.g. ['Refund', 'COVID']

    Output (df):
        - Show the closest matching category for each text
        - Columns: ['Match confidence (lower is better)', 'Matched name', 'Original name']

    Resource: https://towardsdatascience.com/fuzzy-matching-at-scale-84f2bfd0c536
    """

    print('Vecorizing the data - this could take a few minutes for large datasets...')
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
    tfidf = vectorizer.fit_transform(category_keywords)
    print('Vecorizing completed...')

    nbrs = NearestNeighbors(n_neighbors=1, n_jobs=-1).fit(tfidf)

    t1 = time.time()
    print('getting nearest n...')
    distances, indices = getNearestN(tweet_texts, vectorizer, nbrs)
    t = time.time()-t1
    print("COMPLETED IN:", t)
    tweet_texts = list(tweet_texts) #need to convert back to a list

    print('finding matches and building dataframe...')
    processed_distances = [round(distances[i][0],2) for i in range(len(indices))]
    matched_category_names = [category_names[i[0]] for i in indices]
    original_tweet = [tweet_texts[i] for i in range(len(indices))]

    matches = pd.DataFrame({'Match confidence (lower is better)': processed_distances,
                            'Matched category name': matched_category_names,
                            'Original name': original_tweet})

    return matches

def createNew_tweets_df(category_names, matches_df, tweets_df):
    """
    Function: Convert matches into a dataframe accepted by SEAT project

    Inputs:
        - matches_df (df): The output of start(...)
        - tweets_df (df):
            - Necessary columns: ['id', 'text']
            - Output of utils.py from SEAT project
    """

    def get_confidence(text, matches_df):

        return matches_df[matches_df['Original name'] == text]['Match confidence (lower is better)'].tolist()[0]

    def if_category(text, category, matches_df):

        text_category = matches_df[matches_df['Original name'] == text]['Matched category name'].tolist()[0]

        if text_category == category:
            return 1
        else:
            return 0

    tweets_df['Match Confidence (Lower is better)'] = tweets_df['text'].apply(lambda x: get_confidence(x, matches_df))

    for category in category_names:
        tweets_df[category] = tweets_df['text'].apply(lambda x: if_category(x, category, matches_df))

    return tweets_df

def createAnalysis(final_df, category_names):

    L_final = []
    for name in category_names:
        category_if = [-1 if i == 0 else i for i in final_df[name].tolist()]
        L_final.append(category_if)

    L_train = [list(x) for x in list(zip(*L_final))]
    lfs = [LabelingFunction(name=name, f=None) for name in category_names]

    return LFAnalysis(L=np.array(L_train), lfs=lfs).lf_summary()

def start_NLPLF(tweets_df, keyword_groups={}, **kwargs):
    """
    Function: Wrapper for the whole NLP LabelingFunction program
    Input:
        - tweets_df: Same format as in utils.py for SEAT program
        - keyword_groups
        - label: A useless variable (for now)

    Output: (Same format as snorkelLF.py in SEAT program for standardisation)
        - final_df
        - analysis: Generated by Snorkel's LFAnalysis
    """

    tweet_texts = tweets_df['text'].tolist()
    tweet_texts = list(dict.fromkeys(tweet_texts)) ## Remove duplicates

    category_names = list(keyword_groups.keys())
    category_keywords = list(keyword_groups.values())
    category_keywords = [' '.join(words) if type(words) == list else words for words in category_keywords]

    matches_df = NLP_matching(tweet_texts, category_keywords, category_names)

    final_df = createNew_tweets_df(category_names, matches_df, tweets_df)

    analysis = createAnalysis(final_df, category_names)

    return final_df, analysis

if __name__ == '__main__':
##    names =  pd.read_csv('messy org names.csv',encoding='latin')
##    org_column = 'buyer' #column to match against in the messy data
##    #tweet_texts = set(names[org_column].values) # set used for increased performance
##    tweet_texts = names[org_column].tolist()
##
##    clean_org_names = pd.read_excel('Gov Orgs ONS.xlsx')
##    clean_org_names = clean_org_names.iloc[:, 0:6]
##    category_keywords = clean_org_names['Institutions'].unique()
##
##    matches = start(tweet_texts, category_keywords, clean_org_names)

    tweets_df = pd.read_csv('tweets.csv')
    keyword_groups={'refund':['refund', 'cancel', 'cancelled','canceled'],
                    'COVID':['COVID','virus','coronavirus']}

    a_df, analysis = start_NLPLF(tweets_df, keyword_groups=keyword_groups, label=1)


##    tweet_texts = tweets_df['text'].tolist()
##    tweet_texts = list(dict.fromkeys(tweet_texts)) ## Remove duplicates
##
##    category_keywords = ['refund cancel cancelled', 'COVID virus coronavirus']
##    category_names = ['Refund', 'COVID']
##
##    matches_df = NLP_matching(tweet_texts, category_keywords, category_names)
##
##    final_df = createNew_tweets_df(category_names, matches_df, tweets_df)
##
##    analysis = createAnalysis(final_df, category_names)
