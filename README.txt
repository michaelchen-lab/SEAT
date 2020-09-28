SEAT Web App

How it works

This is a sentiment analysis tool meant to help users extract tweet data on their interested topic, and run sentiment analysis on that data.

Step 1: Extraction of tweets through Twitter API using keywords chosen by users

Step 2: Filter out irrelevant data and discard them using keywords chosen by users

Step 3: Categorise relevant data using topics chosen by users, and their corresponding keywords.

Step 4: Sentiment analysis is performed using pre-trained NLP model(s)

Result: A final report is generated containing sentiment analysis results.

Instructions on Running Django project

1. Enter virtual environment 

2. Enter Twitter consumer key and consumer secret key into env variables
   ('TWITTER_CONSUMER_KEY' and 'TWITTER_CONSUMER_SECRET')

3. Edit database settings in /projects/settings.py

2. Enter 'python manage.py runserver'

3. Go to http://127.0.0.1:8000/user/login 
   (Could be a different root url. CMD should display the applicable one)


