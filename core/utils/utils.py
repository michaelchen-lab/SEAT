import pandas as pd
import numpy as np

from .twitterApi import twitterApi
from .snorkelLF import startSnorkelLabeling
from .NLPLF import start_NLPLF
from .bokehGraphing import *
from .sentimentAnalysisModels import *

def formData_to_query(data):
    try:
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

        if query == '':
            return 'error'

    except:
        return 'error'

    return query

def formData_to_filter(data):
    try:
        keywordGroups = {}
        for i in range(10):
            if 'inputName'+str(i) in data.keys() and 'inputKeywords'+str(i) in data.keys():
                keywords = [keyword.lstrip().rstrip().lower() for keyword in data['inputKeywords'+str(i)].split(';')]
                #keywords = [' '+word+' ' for word in keywords]

                keywordGroups[data['inputName'+str(i)]] = keywords

        if keywordGroups == {}:
            return 'error'

    except:
        return 'error'

    return keywordGroups

def tweets_to_df(report, add_ons=[]):

    df = pd.DataFrame({
        'id':[tweet.tweet_id for tweet in report.tweet_set.all()],
        'text':[tweet.text for tweet in report.tweet_set.all()],
        'pub_date':[tweet.pub_date for tweet in report.tweet_set.all()]},
        dtype='object'
    )

    for var in add_ons:
        if var == 'is_relevant':

            df['is_relevant'] = [tweet.is_relevant for tweet in report.tweet_set.all()]

        elif var == 'categories':

            for cat in report.tweetcategory_set.all():
                df[cat.name] = np.where(df['id'].isin([tweet.tweet_id for tweet in cat.tweets.all()]), 'TRUE', 'FALSE')
            del df['Non-Categorised']

        elif var == 'sentiment':

            for sentimentType in report.tweet_set.first().sentiment.keys():
                df[sentimentType+' Sentiment'] = [tweet.sentiment[sentimentType] for tweet in report.tweet_set.all()]

    return df

def filterSentimentTest(report):
    sentimentTypes = list(report.tweet_set.first().sentiment.keys())

    tweetsByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    countsByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    for sentimentType in sentimentTypes:

        negativeFilter = {'sentiment__'+sentimentType+'__lt': 0}
        tweetsByType[sentimentType].update({'negative':report.tweet_set.filter(**negativeFilter)})
        countsByType[sentimentType].update({'negative':report.tweet_set.filter(**negativeFilter).count()})

        positiveFilter = {'sentiment__'+sentimentType+'__gt': 0}
        tweetsByType[sentimentType].update({'positive':report.tweet_set.filter(**positiveFilter)})
        countsByType[sentimentType].update({'positive':report.tweet_set.filter(**positiveFilter).count()})

        neutralFilter = {'sentiment__'+sentimentType: 0}
        tweetsByType[sentimentType].update({'neutral':report.tweet_set.filter(**neutralFilter)})
        countsByType[sentimentType].update({'neutral':report.tweet_set.filter(**neutralFilter).count()})

    ## Get average value by sentiment analysis type
    sentiments = [t.sentiment for t in report.tweet_set.all()]

    avgByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    for type in sentimentTypes:
        avgByType[type] = sum([sentiment[type] for sentiment in sentiments]) / len(sentiments)

    return tweetsByType, countsByType, avgByType

def filterSentiment(tweets):
    sentimentTypes = list(tweets.first().sentiment.keys())

    tweetsByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    countsByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    for sentimentType in sentimentTypes:

        negativeFilter = {'sentiment__'+sentimentType+'__lt': 0}
        tweetsByType[sentimentType].update({'negative':tweets.filter(**negativeFilter)})
        countsByType[sentimentType].update({'negative':tweets.filter(**negativeFilter).count()})

        positiveFilter = {'sentiment__'+sentimentType+'__gt': 0}
        tweetsByType[sentimentType].update({'positive':tweets.filter(**positiveFilter)})
        countsByType[sentimentType].update({'positive':tweets.filter(**positiveFilter).count()})

        neutralFilter = {'sentiment__'+sentimentType: 0}
        tweetsByType[sentimentType].update({'neutral':tweets.filter(**neutralFilter)})
        countsByType[sentimentType].update({'neutral':tweets.filter(**neutralFilter).count()})

    ## Get average value by sentiment analysis type
    sentiments = [t.sentiment for t in tweets]

    avgByType = dict(zip(sentimentTypes, [{} for i in sentimentTypes]))
    for type in sentimentTypes:
        avgByType[type] = sum([sentiment[type] for sentiment in sentiments]) / len(sentiments)

    return tweetsByType, countsByType, avgByType

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

def labelingWrapper(df, keyword_groups={}, label=0, l_type='filter'):

    assert type(keyword_groups) == dict

    if l_type == 'NLP_Categorise':
        df, analysis = start_NLPLF(df, keyword_groups=keyword_groups, label=label, l_type=l_type)
    else:
        df, analysis = startSnorkelLabeling(df, keyword_groups=keyword_groups, label=label, l_type=l_type)

    return df, analysis

def graphWrapper(type='', data='', paletteType=''):

    if type == 'pieChart':
        script, div = drawPieChart(data, paletteType=paletteType)

    return script, div

def nlpWrapper(formData, tweets):

    assert type(formData) == dict
    assert type(tweets) == dict ## {tweet_id:text, ...}

    tweet_sentiments = dict(zip(list(tweets.keys()), [{} for i in list(tweets.keys())]))

    if 'nltk' in formData:
        nltkSentiments = dict(zip(list(tweets.keys()), nltkSentiment(list(tweets.values()))))

        for tweet_id, sentiment in nltkSentiments.items():
            tweet_sentiments[tweet_id].update({'nltk':sentiment})

    if 'textblob' in formData:
        textblobSentiments = dict(zip(list(tweets.keys()), textBlobSentiment(list(tweets.values()))))

        for tweet_id, sentiment in textblobSentiments.items():
            tweet_sentiments[tweet_id].update({'textblob':sentiment})

    avg_sentiments = [sum(list(sentiments.values())) / len(list(sentiments.values())) for sentiments in list(tweet_sentiments.values())]
    avg_sentiments = dict(zip(list(tweets.keys()), avg_sentiments))
    for tweet_id, sentiment in avg_sentiments.items():
        tweet_sentiments[tweet_id].update({'aggregate':sentiment})

    return tweet_sentiments

if __name__ == '__main__':
    df = twitterApiWrapper(q='@CarnivalCruise refund', count=200)
