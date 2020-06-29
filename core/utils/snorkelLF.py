import pandas as pd
import re

from snorkel.labeling import labeling_function, LabelingFunction
from snorkel.labeling import PandasLFApplier
from snorkel.labeling import LFAnalysis
from snorkel.labeling.model import MajorityLabelVoter, LabelModel

ABSTAIN = -1
RELEVANT = 1
IRRELEVANT = 0

def keyword_lookup(x, keywords, label):
    if any(word in x.text.lower() for word in keywords):
        return label
    return ABSTAIN

def regex_keyword_lookup(x, keywords, label):
    if any(re.search(r'\W'+word+r'\W', x.text, flags=re.I) for word in keywords):
        return label
    return ABSTAIN

def make_keyword_lf(lf_name, keywords, label=IRRELEVANT):
    return LabelingFunction(
        name=lf_name,
        f=regex_keyword_lookup,
        resources=dict(keywords=keywords, label=label),
    )

def get_L_final_filter(L_train, method='model'):
    L_final = []

    if len(L_train[0]) < 3:
        method = 'absolute'
    else:
        method = 'model'

    ## TEMPORARY MEASURE
    method = 'absolute'
    ##

    if method == 'absolute':
        ## Absolute Method: Any 'irrelevant' keywords matched will be flagged as irrelevant
        for array in L_train:
            if 0 in array:
                L_final.append(0)
            else:
                L_final.append(1)
    else:
        ## Label Model
        label_model = LabelModel(cardinality=2, verbose=True)
        label_model.fit(L_train=L_train, n_epochs=500, log_freq=100, seed=123)
        L_final = label_model.predict(L=L_train,return_probs=False)

    return L_final

def get_L_final_categorise(L_train):
    L_train = [list(x) for x in zip(*L_train)]
    L_train = [[0 if value == -1 else value for value in value_list] for value_list in L_train]

    return L_train

def startSnorkelLabeling(df, keyword_groups={}, label=IRRELEVANT, l_type='SnorkelFilter'):
    '''
    Function: Filter words for user
    Inputs:
        - df: tweets DataFrame (columns: [id, text])
        - keywords: Keyword group and its relevant keywords
          E.g. {'usps': ['postal service', 'usps'], 'invest': ['invest','portfolio','stock']}
    Outputs:
        - a_df: Categorised Data (e.g. columns = ['id', 'tweets', 'Refund', 'COVID'])
        - analysis: Snorkel Labeling Function statistics
    '''

    lfs = []
    for name, keywords in keyword_groups.items():
        lfs.append(make_keyword_lf(lf_name=name, keywords=keywords, label=label))

    applier = PandasLFApplier(lfs=lfs)
    L_train = applier.apply(df=df)

    if l_type == 'SnorkelFilter': # For spam detection (Step 2)
        L_final = get_L_final_filter(L_train)
        df['relevance'] = L_final

    elif l_type == 'SnorkelCategorise': # For categorising tweets (Step 3)
        L_final = get_L_final_categorise(L_train)

        L_final_with_names = dict(zip(keyword_groups.keys(), L_final))
        for name, L_values in L_final_with_names.items():
            df[name] = L_values

    analysis = LFAnalysis(L=L_train, lfs=lfs).lf_summary()

    #return L_train, L_final, df, analysis
    return df, analysis

if __name__ == '__main__':

##    df = pd.read_csv('tweets.csv')
##
##    keyword_usps = make_keyword_lf(lf_name='keyword_usps', keywords=['postal service', 'postalservice', 'usps'])
##    keyword_invest = make_keyword_lf(lf_name='keyword_invest', keywords=['invest','stock','portfolio'])
##    lfs = [keyword_usps, keyword_invest]
##
##    applier = PandasLFApplier(lfs=lfs)
##    L_train = applier.apply(df = df)
##
##    L_final = get_L_final(L_train)
##    df['relevance'] = L_final

    df = pd.read_csv('tweets.csv')
    keyword_groups={'refund':['refund', 'cancel', 'cancelled',
                    'canceled'], 'COVID-19':['COVID','virus','coronavirus']}

    a_df, analysis = startLabeling(df, keyword_groups=keyword_groups,
                                   label=RELEVANT, l_type='SnorkelCategorise')
