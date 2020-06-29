import nltk
from textblob import TextBlob
#import flair

nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def nltkSentiment(sentences):

    assert type(sentences) == list

    sid = SentimentIntensityAnalyzer()
    sentiments = [sid.polarity_scores(sentence)['compound'] for sentence in sentences]

    return sentiments

def textBlobSentiment(sentences):

    assert type(sentences) == list

    sentiments = [TextBlob(sentence).sentiment.polarity for sentence in sentences]

    return sentiments

## Results are rather pathetic.
##def flairSentiment(sentence):
##
##    flair_sentiment = flair.models.TextClassifier.load('en-sentiment')
##
##    s = flair.data.Sentence(sentence)
##    flair_sentiment.predict(s)
##    total_sentiment = s.labels
##
##    return total_sentiment
