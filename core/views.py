from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone
from django.db import transaction

import pandas as pd

from .forms import SignUpForm
from .models import Report, Tweet, tweetCategory
from .utils.utils import *

def signupViewBackup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()
            user.profile.first_name = form.cleaned_data.get('first_name')
            user.profile.last_name = form.cleaned_data.get('last_name')
            user.profile.email = form.cleaned_data.get('email')
            user.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('core:home')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})

def signupView(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('core:home')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

def loginView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            ## login user
            #return HttpResponseRedirect(reverse('core:home'))
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            login(request, authenticate(username=username, password=password))
            return redirect('core:home')
    else:
        logout(request)
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form':form})

@login_required(login_url='/user/login')
def homeView(request):

    ## Create alert
    data = {}
    if request.session.get('error', None) != None:
        data.update(request.session.get('error'))
        del request.session['error']

    ## Check for report buttons
    button = request.POST.get('finishButton','')
    if button != '':
        report = Report.objects.get(id=request.session['reportID'])
        report.pipeline_step = 'completed'
        report.save()
        data.update({'success_alert':'Your report ('+button+') has been completed and saved!'})

    button = request.POST.get('saveResumeButton','')
    if button != '':
        report = Report.objects.get(id=request.session['reportID'])
        data.update({'success_alert':'Your report ('+button+') has been saved! You may continue working on this report at '+report.pipeline_step+'.'})

    button = request.POST.get('discardButton','')
    if button != '':
        report = Report.objects.get(id=request.session['reportID'])
        report.delete()
        data.update({'success_alert':'Your incomplete report ('+button+') has been discarded!'})

    button = request.POST.get('deleteButton', '')
    if button != '':
        report = Report.objects.get(id=button)
        report.delete()
        data.update({'primary_alert':'Your report ('+report.name+') has been deleted!'})

    if 'reportID' in request.session:
        del request.session['reportID']

    return render(request, 'core/home.html', data)

@login_required(login_url='/user/login')
def myReportsView(request):
    data = {}

    user = User.objects.get(id=request.user.id)
    reports = Report.objects.filter(user=user)

    allReportData = []
    for report in reports:
        reportData = {
            'name':report.name,
            'description':report.description,
            'created_at':report.pub_date.strftime('%Y-%m-%d %H:%M')
        }
        if report.pipeline_step == 'completed':
            reportData['completed'] = True

        allReportData.append(reportData)
    allReportDataChunks = [allReportData[x:x+2] for x in range(0, len(allReportData), 2)]
    print(allReportDataChunks)

    data.update({'allReportDataChunks':allReportDataChunks})
    return render(request, 'core/myReports.html', data)

@login_required(login_url='/user/login')
def reportView(request, report_name):
    data = {}

    try:
        user = User.objects.get(id=request.user.id)
        report = Report.objects.get(user=user, name=report_name)

        assert report.pipeline_step == 'completed'
    except:
        return redirect('core:home')

    categories = [cat.name for cat in report.tweetcategory_set.all()]
    categories = ['All'] + categories
    sentimentType = list(report.tweet_set.first().sentiment.keys())

    data.update({'categories':categories, 'sentimentType':sentimentType })

    if request.method == "POST":
        formData = {k:v[0] for k,v in dict(request.POST).items() if v[0] != ''}

        visualData = {}
        for catName in categories:
            if catName in formData: # category is selected by user for visualization
                if catName == 'All':
                    tweetsInCat = report.tweet_set.all()
                else:
                    tweetsInCat = report.tweetcategory_set.get(name=catName).tweets.all()

                if tweetsInCat:

                    tweetsByType, countsByType, avgByType = filterSentiment(tweetsInCat)
                    # Keep only selected sentiment types
                    countsByType = {sentType:sentiments for sentType,sentiments in countsByType.items() if sentType in formData}
                    avgByType = {sentType:sentiments for sentType,sentiments in avgByType.items() if sentType in formData}

                    visualByType = {}
                    for sentType, sentCount in countsByType.items():
                        visualByType[sentType] = dict(zip(['script', 'div'], list(graphWrapper(type='pieChart', data=sentCount, paletteType='Set2'))))

                    visualData[catName] = visualByType

        data['visualData'] = visualData

    # 'reportView':'True'
    data.update({
        'report':report,
        'countTweets':report.tweet_set.count(),
        'created_at':report.pub_date.strftime('%Y-%m-%d %H:%M'),})
    return render(request, 'core/report.html', data)

@login_required(login_url='/user/login')
def resumeReportView(request, report_name):
    data = {}

    try:
        user = User.objects.get(id=request.user.id)
        report = Report.objects.get(user=user, name=report_name)

        assert report.pipeline_step != 'completed'
    except:
        return redirect('core:home')

    request.session['reportID'] = report.id

    if report.pipeline_step in ['step-one']:
        return redirect('core:step-one')
    elif report.pipeline_step in ['step-one-results', 'step-two']:
        return redirect('core:step-two')
    elif report.pipeline_step in ['step-two-results', 'step-three']:
        return redirect('core:step-three')
    elif report.pipeline_step in ['step-three-results', 'step-four', 'step-four-results']:
        return redirect('core:step-four')


@login_required(login_url='/user/login')
def stepZeroView(request):

    ## Create alert
    data = {}
    if request.session.get('error', None) != None:
        data.update(request.session.get('error'))
        del request.session['error']

    return render(request, 'core/stepZero.html', data)

@login_required(login_url='/user/login')
def stepOneView(request):
    data = {}

    # if request.POST.get('name', None) == None:
    #     request.session['error'] = {'danger_alert':'Error occured when accessing Pipeline Step 1.'}
    #     return redirect('core:home')

    if 'reportID' not in request.session: ## Report does not exist
        #if Report.objects.filter(name=request.POST.get('name')).exists():
        #    request.session['error'] = {'danger_alert':'The report name already exits. Please enter a unique report name.'}
        #    return redirect('core:step-zero')

        user = User.objects.get(id=request.user.id)
        report = Report(
            user=user,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            pub_date=timezone.now()
        )
        try:
            report.save()
            request.session['reportID'] = report.id
        except:
            print('did not save')
    else:
        ## 'Revise Query Options' button was triggered
        report = Report.objects.get(id=request.session['reportID'])
        report.tweet_set.all().delete()

        #data.update({'primary_alert':'Query options have been reset. Please re-enter your queries.'})

    ## Create alert
    if request.session.get('error', None) != None:
        data.update(request.session.get('error'))
        del request.session['error']

    report.pipeline_step = 'step-one'
    report.save()
    data.update({'report':report})
    return render(request, 'core/stepOne.html', data)

@login_required(login_url='/user/login')
def stepOneResultsView(request):
    if request.method == 'POST':
        try:
            report = Report.objects.get(id=request.session['reportID'])
            #assert report.pipeline_step == 'step-one'
        except:
            return redirect('core:step-zero')

        ## Get query from HTML form
        data = {k:v[0] for k,v in dict(request.POST).items() if v[0] != ''}
        query = formData_to_query(data)
        # If utils fails to parse form data
        if query == 'error':
            request.session['error'] = {'danger_alert':'An error occured. Each row must either be completely filled or left empty.'}
            return redirect('core:step-one')

        report.query = query

        ## Extract and save tweets
        tweets_df = twitterApiWrapper(q=query, count=data['tweetsNumber'])

        tweets_df['pub_date'] = [timezone.make_aware(date) for date in tweets_df['pub_date'].tolist()]
        tweets = [Tweet(report_id=report.id, **tweet_dict) for tweet_dict in tweets_df.to_dict('records')]
        report.tweet_set.bulk_create(tweets)

        report.pipeline_step = 'step-one-results'
        report.save()
        return render(request, 'core/stepOneResults.html', {'report': report, 'sampleTweets':report.tweet_set.all()[:15], 'countTweets':report.tweet_set.count()})

@login_required(login_url='/user/login')
def stepTwoView(request):
    data = {}

    try:
        report = Report.objects.get(id=request.session['reportID'])
        #assert report.pipeline_step == 'step-one-results'
    except:
        return redirect('core:home')

    if request.method == 'POST':

        ## Check for 'Revice Filter Queries' button from stepTwoResults
        changeButton = request.POST.get('changeButton','')
        if changeButton == 'True':
            report.relevanceKeywords = ''
            report.tweet_set.all().update(is_relevant=None)

            data.update({'primary_alert':'Filter queries have been reset. Please re-enter your queries.'})

        report.pipeline_step = 'step-two'
        report.save()
        data.update({'report':report})
    else: # 'GET' method

        ## Create alert
        if request.session.get('error', None) != None:
            data.update(request.session.get('error'))
            del request.session['error']

        report.pipeline_step = 'step-two'
        report.save()
        data.update({'report':report})

    return render(request, 'core/stepTwo.html', data)

@login_required(login_url='/user/login')
def stepTwoResultsView(request):
    if request.method == 'POST':
        try:
            report = Report.objects.get(id=request.session['reportID'])
            #assert report.pipeline_step == 'step-two'
        except:
            return redirect('core:home')

        ## Get form data and tweets DataFrame
        data = {k:v[0] for k,v in dict(request.POST).items() if v[0] != ''}
        keywordGroups = formData_to_filter(data)

        # If utils fails to parse form data
        if keywordGroups == 'error':
            request.session['error'] = {'danger_alert':'An error occured. Each row must either be completely filled or left empty. Please check your query against the format below.'}
            return redirect('core:step-two')

        df = tweets_to_df(report)
        ## Label tweets DataFrame using keyword groups
        filtered_df, label_analysis = labelingWrapper(df, keyword_groups=keywordGroups, label=0, l_type='SnorkelFilter')

        ## Update database for relevance data
        irrelevant_ids = filtered_df[filtered_df.relevance == 0].id.tolist()
        report.tweet_set.filter(tweet_id__in=irrelevant_ids).update(is_relevant='0')
        relevant_ids = filtered_df[filtered_df.relevance == 1].id.tolist()
        report.tweet_set.filter(tweet_id__in=relevant_ids).update(is_relevant='1')

        report.relevanceKeywords = keywordGroups

        ## get display data
        irrelevant_names = dict(zip(label_analysis.index.tolist(), label_analysis.Coverage.tolist()))
        #overall_relevance = filtered_df['relevance'].value_counts(normalize=True) * 100
        overall_relevance = filtered_df['relevance'].value_counts()
        graphData = []
        for name, value in irrelevant_names.items():
            graphData.append({'Irrelevant (%)':value*100, 'Relevant (%)':(1-float(value))*100})

        ## Get graph scripts and divs
        try:
            mainScript, mainDiv = graphWrapper(type='pieChart', data={'Irrelevant':overall_relevance.at[0], 'Relevant':overall_relevance.at[1]}, paletteType='Set1')
        except:
            ## where there are no irrelevant tweets
            mainScript, mainDiv = graphWrapper(type='pieChart', data={'Irrelevant':0, 'Relevant':overall_relevance.at[1]}, paletteType='Set1')

        componentScripts, componentDivs = [], []
        for data in graphData:
            script, div = graphWrapper(type='pieChart', data=data, paletteType='Set2')

            componentScripts.append(script)
            componentDivs.append(div)

        componentDivs_with_description = [list(x) for x in zip(list(keywordGroups.values()), componentDivs)]
        all_componentDivs = dict(zip(label_analysis.index.tolist(), componentDivs_with_description))

        report.pipeline_step = 'step-two-results'
        report.save()
        data = {
            'report':report,
            'mainScript':mainScript,
            'mainDiv':mainDiv,
            'componentScripts':componentScripts,
            'componentDivs':all_componentDivs,
            'irrelevant_sampleTweets':report.tweet_set.filter(is_relevant=0)[:10]
        }
        return render(request, 'core/stepTwoResults.html', data)

@login_required(login_url='/user/login')
def stepThreeView(request):
    data = {}

    try:
        report = Report.objects.get(id=request.session['reportID'])
        #assert report.pipeline_step == 'step-two-results'
    except:
        return redirect('core:home')

    if request.method == 'POST':

        ## Check for 'Revice Filter Queries' button from stepThreeResults
        changeButton = request.POST.get('changeButton','')
        if changeButton == 'True':
            report.tweetcategory_set.all().delete()
            report.tweetCategory_method = ''

        ## Check for 'skip' button from stepTwo
        if request.POST.get('skipButton', None) != None:
            data.update({'primary_alert':'Step 2 has been skipped.'})

        ## Delete irrelevant tweets
        report.tweet_set.filter(is_relevant=0).delete()

    else: ## 'GET' method

        ## Create alert
        if request.session.get('error', None) != None:
            data.update(request.session.get('error'))
            del request.session['error']

    report.pipeline_step = 'step-three'
    report.save()
    data.update({'report':report})

    return render(request, 'core/stepThree.html', data)

@login_required(login_url='/user/login')
def stepThreeResultsView(request):
    if request.method == 'POST':
        try:
            report = Report.objects.get(id=request.session['reportID'])
            #assert report.pipeline_step == 'step-three'
        except:
            return redirect('core:home')

        ## Get form data and tweets DataFrame
        formData = {k:v[0] for k,v in dict(request.POST).items() if v[0] != ''}
        keywordGroups = formData_to_filter(formData)

        # If utils fails to parse form data
        if keywordGroups == 'error':
            request.session['error'] = {'danger_alert':'An error occured. Each row must either be completely filled or left empty. Please check your query against the format below.'}
            return redirect('core:step-three')
        elif 'Non-Categorised' in list(keywordGroups.keys()):
            request.session['error'] = {'danger_alert':"An error occured. The category name 'Non-Categorised' is reserved for uncategorised tweets and cannot be used."}
            return redirect('core:step-three')

        df = tweets_to_df(report)
        ## Label tweets DataFrame using keyword groups
        filtered_df, label_analysis = labelingWrapper(df, keyword_groups=keywordGroups, label=1, l_type=formData['method'])

        ## Update database to add categories ##
        categorised_tweet_ids = []
        for categoryName, categoryKeywords in keywordGroups.items():
            cat = report.tweetcategory_set.create(name=categoryName, keywords=categoryKeywords)

            tweet_ids = filtered_df[filtered_df[categoryName] == 1]['id'].tolist()
            tweets = report.tweet_set.filter(tweet_id__in=tweet_ids)
            cat.tweets.add(*tweets)

            categorised_tweet_ids.extend(tweet_ids)

        # Add all uncategorised tweets to 'Non-Categorised' category
        categorised_tweet_ids = list(dict.fromkeys(categorised_tweet_ids))
        all_tweet_ids = [tweet.tweet_id for tweet in report.tweet_set.all()]
        uncategorised_tweet_ids = [id for id in all_tweet_ids if id not in categorised_tweet_ids]

        cat = report.tweetcategory_set.create(name='Non-Categorised')
        tweets = report.tweet_set.filter(tweet_id__in=uncategorised_tweet_ids)
        cat.tweets.add(*tweets)

        ## Visualize categorization ##
        category_with_percentage = dict(zip(label_analysis.index.tolist(), label_analysis.Coverage.tolist()))
        category_with_percentage['Non-Categorised'] = len(uncategorised_tweet_ids) / len(all_tweet_ids)
        graphData = []
        for name, value in category_with_percentage.items():
            if name != 'Non-Categorised':
                graphData.append({name+' (%)':value*100, 'NOT '+name+' (%)':(1-float(value))*100})
            else:
                graphData.append({name+' (%)':value*100, 'Categorised (%)':(1-float(value))*100})

        componentScripts, componentDivs = [], []
        for data in graphData:
            script, div = graphWrapper(type='pieChart', data=data, paletteType='Set1')

            componentScripts.append(script)
            componentDivs.append(div)

        keywordGroups['Non-Categorised'] = '' ## Create empty description for 'Non-Categorised' category
        componentDivsWith_description = [list(x) for x in zip(list(keywordGroups.values()), componentDivs)]
        componentDivsWith_descripton_name = dict(zip(category_with_percentage.keys(), componentDivsWith_description))

        ## Get sample tweets by category ##
        sampleTweets_by_cat = [category.tweets.order_by('?')[:10] for category in report.tweetcategory_set.all()]
        sampleTweets_with_cat = dict(zip([cat.name for cat in report.tweetcategory_set.all()], sampleTweets_by_cat))

        try:
            del sampleTweets['Non-Categorised']
        except:
            print('No Non-Categorised when extracting sampleTweets')

        # SAMPLE INPUTS
        # Refund
        # refund; cancel; cancelled; canceled
        # COVID-19
        # covid; virus; coronavirus

        report.pipeline_step = 'step-three-results'
        if formData['method'] == 'SnorkelCategorise':
            report.tweetCategory_method = 'Absolute Method'
        else:
            report.tweetCategory_method = 'NLP Method'
        report.save()
        data = {
            'report':report,
            'componentScripts':componentScripts,
            'componentDivs':componentDivsWith_descripton_name,
            'sampleTweets':sampleTweets_with_cat
        }
        return render(request, 'core/stepThreeResults.html', data)
    else:
        return redirect('core:home')

@login_required(login_url='/user/login')
def stepFourView(request):
    data = {}

    try:
        report = Report.objects.get(id=request.session['reportID'])
        #assert report.pipeline_step == 'step-two-results'
    except:
        return redirect('core:home')

    ## Check for 'Revise Analysis Options' button from stepThreeResults
    changeButton = request.POST.get('changeButton','')
    if changeButton == 'True':
        report.tweet_set.all().update(sentiment={})

    ## Check for 'skip' button from stepTwo
    if request.POST.get('skipButton', None) != None:
        data.update({'primary_alert':'Step 3 has been skipped.'})

    report.pipeline_step = 'step-four'
    report.save()
    data.update({'report':report})

    return render(request, 'core/stepFour.html', data)

@login_required(login_url='/user/login')
def stepFourResultsView(request):
    data = {}

    if request.method == 'POST':
        try:
            report = Report.objects.get(id=request.session['reportID'])
            assert report.pipeline_step == 'step-four' or report.pipeline_step == 'step-four-results'
        except:
            return redirect('core:home')

        ## Get form data and tweets data
        formData = {k:v[0] for k,v in dict(request.POST).items() if v[0] != ''}
        tweets = dict(zip([t.pk for t in report.tweet_set.all()], [t.text for t in report.tweet_set.all()]))

        ## Perform sentiment analysis
        tweet_sentiments = nlpWrapper(formData, tweets)

        ## Update tweets
        updates = report.tweet_set.all().in_bulk()
        for tweet_id, sentiment in tweet_sentiments.items():
            updates[tweet_id].sentiment = sentiment
        report.tweet_set.bulk_update(updates.values(), ['sentiment'])

        ## Get visualization data
        tweetsByType, countsByType, avgByType = filterSentiment(report.tweet_set.all())

        # Get mainDiv and componentDiv
        mainScript, mainDiv = graphWrapper(type='pieChart', data=countsByType['aggregate'], paletteType='Set1')
        del countsByType['aggregate']

        componentScripts, componentDivs = [], []
        for data in countsByType.values():

            script, div = graphWrapper(type='pieChart', data=data, paletteType='Set2')
            componentScripts.append(script)
            componentDivs.append(div)

        componentDivs_withName = dict(zip(countsByType.keys(), componentDivs))

        report.pipeline_step = 'step-four-results'
        report.save()
        data.update({
            'report':report,
            'mainScript':mainScript,
            'mainDiv':mainDiv,
            'componentScripts':componentScripts,
            'componentDivs':componentDivs_withName,
        })
        return render(request, 'core/stepFourResults.html', data)

@login_required(login_url='/user/login')
def sampleTweetsFileView(request, report_name):
    if request.method == 'POST':
        try:
            report = Report.objects.get(id=request.session['reportID'])
            exportType = request.POST.get('exportButton','')
            assert exportType != ''
        except:
            return redirect('core:home')

        exportType = exportType.split(";")
        if exportType[0] == 'raw':
            sampleTweets = tweets_to_df(report)
        elif exportType[0] == 'with_is_relevant':
            sampleTweets = tweets_to_df(report, add_ons=['is_relevant'])
        elif exportType[0] == 'with_categories':
            sampleTweets = tweets_to_df(report, add_ons=['categories'])
        elif exportType[0] == 'with_sentiment':
            sampleTweets = tweets_to_df(report, add_ons=['sentiment'])
        elif exportType[0] == 'with_all':
            sampleTweets = tweets_to_df(report, add_ons=['categories', 'sentiment'])

        if exportType[1] != 'all':
            sampleTweets = sampleTweets.sample(n=int(exportType[1]))

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=sampleTweets.csv'

        #sampleTweets.to_csv(path_or_buf=response,sep=',',float_format='%.2f',index=False)
        sampleTweets.to_csv(path_or_buf=response,sep=',',index=False)

        return response
    else:
        return redirect('core:home')
