from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('login/', views.loginView, name='login'),
    path('', views.homeView, name='home'),
    path('signup/', views.signupView, name='signup'),
    path('my-reports/', views.myReportsView, name='my-reports'),
    path('report/<str:report_name>', views.reportView, name='report'),
    path('resume-report/<str:report_name>', views.resumeReportView, name='resume-report'),
    path('create-report/', views.stepZeroView, name='step-zero'),
    path('create-report/step-1', views.stepOneView, name='step-one'),
    path('create-report/step-1-results', views.stepOneResultsView, name='step-one-results'),
    path('create-report/step-2', views.stepTwoView, name='step-two'),
    path('create_report/step-2-results', views.stepTwoResultsView, name='step-two-results'),
    path('create_report/step-3', views.stepThreeView, name='step-three'),
    path('create_report/step-3-results', views.stepThreeResultsView, name='step-three-results'),
    path('create_report/step-4', views.stepFourView, name='step-four'),
    path('create_report/step-4-results', views.stepFourResultsView, name='step-four-results'),
    path('get_tweets_data/<str:report_name>', views.sampleTweetsFileView, name='sampleTweetsFile'),
]
