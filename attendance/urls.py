from django.urls import path
from .views import AttendanceReportView, DailyStatisticsReportView

urlpatterns = [
    path('report/uncounted', AttendanceReportView.as_view(), name='attendance-report'),
    path('report/statistics', DailyStatisticsReportView.as_view(), name='daily-statistics-report'),

]