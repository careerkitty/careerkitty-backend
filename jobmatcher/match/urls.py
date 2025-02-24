from django.urls import path
from .views import JobDescriptionView, ResumeView, MatchView

urlpatterns = [
    path('job-description/', JobDescriptionView.as_view(), name='job-description'),
    path('resume/', ResumeView.as_view(), name='resume'),
    path('match/', MatchView.as_view(), name='match'),
]
