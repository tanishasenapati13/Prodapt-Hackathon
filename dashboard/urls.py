"""
Dashboard URL configuration.

Routes:
  /dashboard/              → results view (ranked candidate list)
  /dashboard/candidate/<id>/ → candidate detail view (gap analysis)
"""
from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_results, name="results"),
    path("candidate/<int:candidate_id>/", views.candidate_detail, name="candidate_detail"),
]
