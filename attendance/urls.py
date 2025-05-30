from django.urls import path
from .views import AttendanceReportView, DailyStatisticsReportView, HourlyCourseSummaryView, MonthlyCourseSummaryView, FilteredMonthlyCourseSummaryView

urlpatterns = [
    path('report/uncounted', AttendanceReportView.as_view(), name='attendance-report'),
    path('report/statistics', DailyStatisticsReportView.as_view(), name='daily-statistics-report'),
    path('report/course_summary', HourlyCourseSummaryView.as_view(), name='course-summary'),
    path('report/monthly_course_summary', MonthlyCourseSummaryView.as_view(), name='monthly-course-summary'),
    path('report/filtered_monthly_course_summary', FilteredMonthlyCourseSummaryView.as_view(), name='filtered-monthly-course-summary'),
]