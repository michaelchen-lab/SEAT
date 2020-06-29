from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=150)
    bio = models.TextField()

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def update_profile_signal(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    pub_date = models.DateTimeField('date published')

    query = models.CharField(max_length=156, default='')
    relevanceKeywords = JSONField(default=dict)
    tweetCategory_method = models.CharField(max_length=156, default='')
    pipeline_step = models.CharField(max_length=200, default='') ## Step entered IS BEING DONE

    def __str__(self):
        return self.name

class Tweet(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    tweet_id = models.CharField(max_length=50, default='')
    text = models.TextField()
    is_relevant = models.BooleanField(null=True, blank=True)
    pub_date = models.DateTimeField('date published')
    sentiment = JSONField(default=dict)

    #category = models.ManyToManyField(tweetCategory, null=True, blank=True)

    def __str__(self):
        return self.tweet_id

class tweetCategory(models.Model):
    report = models.ForeignKey(Report, blank=False, default=None, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    keywords = models.TextField(null=True, default=None)
    tweets = models.ManyToManyField(Tweet, blank=True)

    def __str__(self):
        return self.name
