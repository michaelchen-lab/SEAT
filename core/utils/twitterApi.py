import tweepy

## Search query operators
## https://developer.twitter.com/en/docs/tweets/search/guides/standard-operators

consumer_key = 'opL9KcZ68AaKhDsNIgC4K1CKS'
consumer_secret = 'TH1SqkwYE4r834T8gwj4TyWxHQkVfi8hxGIDxGW4zJPxHbAcjP'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# search_engine = api.search(q="python", result_type="recent", count=100, lang='en', tweet_mode='extended')

search_engine = api.search(q="@CarnivalCruise", result_type="recent", count=10, lang='en', tweet_mode='extended')
search_results = [result for result in search_engine]

class twitterApi:

    def authenticate(self, consumer_key='', consumer_secret=''):
        ## Authenticate using Twitter API credentials
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        api = tweepy.API(auth)

        self.api = api

    def get_tweets_backup(self, q=0, count='', result_type=0):
        ## Get relevant tweets using query
        ## Note: Only extracts up to 100 tweets

        assert type(q) == str and type(count) == int and type(result_type) == str
        
        search_engine = self.api.search(q=q, result_type=result_type, count=count, lang='en', tweet_mode='extended')
        search_results = [result for result in search_engine]

        self.tweets = [result.full_text for result in search_results]

    def get_tweets(self, q=0, count='', result_type=0):
        ## Get relevant tweets using query

        assert type(q) == str and type(count) == int and type(result_type) == str

        sinceId = None
        max_id = -1
        maxTweets = count
        tweetsPerQry = 100

        tweetCount = 0
        allTweets = []
        while tweetCount < maxTweets:
            if maxTweets - tweetCount < 100:
                tweetsPerQry = maxTweets - tweetCount
            else:
                tweetsPerQry = 100
            try:
                if (max_id <= 0):
                    if (not sinceId):
                        new_tweets = self.api.search(q=q, count=tweetsPerQry, lang='en', tweet_mode='extended')
                    else:
                        new_tweets = self.api.search(q=q, count=tweetsPerQry,
                                                since_id=sinceId, lang='en', tweet_mode='extended')
                else:
                    if (not sinceId):
                        new_tweets = self.api.search(q=q, count=tweetsPerQry,
                                                max_id=str(max_id - 1), lang='en', tweet_mode='extended')
                    else:
                        new_tweets = self.api.search(q=q, count=tweetsPerQry,
                                                max_id=str(max_id - 1),
                                                since_id=sinceId, lang='en', tweet_mode='extended')
                if not new_tweets:
                    print("No more tweets found")
                    break

                new_tweets = [tweet for tweet in new_tweets]
                allTweets.extend(new_tweets)
                                 
                tweetCount += len(new_tweets)
                print("Downloaded {0} tweets".format(tweetCount))
                max_id = new_tweets[-1].id
            except tweepy.TweepError as e:
                # Just exit if any error
                print("some error : " + str(e))
                break

        self.tweets = allTweets

t = twitterApi()
t.authenticate(consumer_key='opL9KcZ68AaKhDsNIgC4K1CKS', consumer_secret='TH1SqkwYE4r834T8gwj4TyWxHQkVfi8hxGIDxGW4zJPxHbAcjP')

# t.get_tweets(q='@Nike', count=20, result_type='mixed')
# t.get_tweets(q='@CarnivalCruise refund', count=20)
