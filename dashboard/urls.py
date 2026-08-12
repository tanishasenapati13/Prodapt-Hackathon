"""
Dashboard URL configuration.

Routes:
  /dashboard/              → results view (ranked candidate list)
  /dashboard/candidate/<id>/ → candidate detail view (gap analysis)
  /dashboard/feedback/     → POST recruiter feedback (Feedback Loop)
"""
from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_results, name="results"),
    path("candidate/<str:candidate_id>/", views.candidate_detail, name="candidate_detail"),
    path("feedback/", views.submit_feedback, name="feedback"),
]

