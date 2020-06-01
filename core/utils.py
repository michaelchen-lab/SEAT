from .utils.twitterApi import twitterApi
from .utils.snorkelLF import startLabeling
from .utils.bokehGraphing import *
import pandas as pd

def formData_to_query(data):
    query = ''
    for i in range(1,6):
        if 'inputContain'+str(i) in data.keys() and 'inputPrefix'+str(i) in data.keys() and 'inputQuery'+str(i) in data.keys():
            containOperators = {'Contains':'', 'Does not contain':'-'}
            contain = containOperators[data['inputContain'+str(i)]]
            prefixOperators = {'NIL':'', '#':'#', '@':'@'}
            prefix = prefixOperators[data['inputPrefix'+str(i)]]

            partQuery = contain+prefix+data['inputQuery'+str(i)]
            query += ' '+partQuery

    query = query.lstrip()

    return query

def formData_to_filter(data):
    keywordGroups = {}
    for i in range(10):
        if 'inputName'+str(i) in data.keys() and 'inputKeywords'+str(i) in data.keys():
            keywords = [keyword.lstrip().rstrip().lower() for keyword in data['inputKeywords'+str(i)].split(';')]

            keywordGroups[data['inputName'+str(i)]] = keywords

    return keywordGroups

def tweets_to_df(report):

    df = pd.DataFrame({
        'id':[tweet.tweet_id for tweet in report.tweet_set.all()],
        'text':[tweet.text for tweet in report.tweet_set.all()],
        'pub_date':[tweet.pub_date for tweet in report.tweet_set.all()]}
    )

    return df

def twitterApiWrapper(q='', count=0):

    t = twitterApi()
    t.authenticate(consumer_key='opL9KcZ68AaKhDsNIgC4K1CKS', consumer_secret='TH1SqkwYE4r834T8gwj4TyWxHQkVfi8hxGIDxGW4zJPxHbAcjP')

    t.get_tweets(q=q, count=int(count), result_type='recent')
    df = pd.DataFrame({
        'tweet_id':[tweet.id for tweet in t.tweets],
        'text':[tweet.full_text for tweet in t.tweets],
        'pub_date':[tweet.created_at for tweet in t.tweets]}
    )

    return df

def labelingWrapper(df, keyword_groups={}):

    assert type(keyword_groups) == dict

    df = startLabeling(df, keyword_groups)

    return df

def bokehWrapper(type='', data=''):

    if type == 'pieChart':
        script, div = drawPieChart(data)

    return script, div

if __name__ == '__main__':
    df = twitterApiWrapper(q='@CarnivalCruise refund', count=200)
