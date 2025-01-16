from django.contrib import admin
from .models import Attendance
from django.db.models import Count

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school_id', 'classification', 'purpose', 'time_in_date')
    list_filter = ('classification', 'purpose', 'time_in_date')
    search_fields = ('full_name', 'school_id')
    readonly_fields = ('id', 'time_in_date')
    
    def get_date_hierarchy(self, request):
        """
        Only set up date_hierarchy if there are valid dates in the database
        """
        if self.date_hierarchy:
            has_dates = self.model.objects.filter(
                time_in_date__isnull=False
            ).exists()
            return self.date_hierarchy if has_dates else None
        return None
    
    date_hierarchy = 'time_in_date'

    def get_queryset(self, request):
        """
        Ensure the queryset excludes any records with null time_in_date
        """
        queryset = super().get_queryset(request)
        return queryset.filter(time_in_date__isnull=False)