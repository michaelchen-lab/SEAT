# SEAT Web App
---

The SEAT Web App is a sentiment analysis web app which aims to democratize sentiment analysis for non-technical users.

## Links
---

### Article
* [Final Report for SEAT](https://drive.google.com/file/d/1aBY6jPdaB1LX5gGpm_dkC82TWwZCj3xs/view?usp=sharing)

### Video
* [Youtube tutorial](https://youtu.be/DpauTl1RduY)

### Report

## How It Works
---

This is a sentiment analysis tool meant to help users extract tweet data on their interested topic, and run sentiment analysis on that data.

**Step 1**: Extraction of tweets through Twitter API using keywords chosen by users

**Step 2**: Filter out irrelevant data and discard them using keywords chosen by users

**Step 3**: Categorise relevant data using topics chosen by users, and their corresponding keywords.

**Step 4**: Sentiment analysis is performed using pre-trained NLP model(s)

## Get Started
---
Setup local Python environment
```
$ virtualenv venv
```
Enter Twitter consumer key and consumer secret key into env variables
```
Environment Variables: 'TWITTER_CONSUMER_KEY' and 'TWITTER_CONSUMER_SECRET'
```

Edit your PostgreSQL database credentials in /projects/settings.py
```
DATABASES = {
    'default': {
        'ENGINE': (engine),
        'NAME': '(name)',
        'USER': '(user)',
        'PASSWORD': '(password)',
        'HOST': '(host URL)',
        'PORT': '(port number)'
    }
}
```

Start Django local server in command line
```
$ python manage.py runserver
```

Go to the localhost URL provided by Django, and have fun exploring SEAT!
