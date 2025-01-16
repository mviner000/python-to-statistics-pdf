from django.urls import path
from .views import AttendanceReportView

urlpatterns = [
    path('api/report/', AttendanceReportView.as_view(), name='attendance-report'),
]