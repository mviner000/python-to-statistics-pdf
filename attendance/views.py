

from django.shortcuts import render
from django.views.generic import View
from django.utils import timezone
from collections import defaultdict
from datetime import datetime
import pandas as pd
from .models import Attendance
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse

class AttendanceReportView(View):
    template_name = 'attendance_report_uncounted_per_day.html'

    def get_classifications(self):
        return [
            'JUNIOR HIGH SCHOOL', 
            'Accountancy, Business and Management (ABM)', 
            'Science, Technology, Engineering and Mathematics', 
            'Humanities and Social Sciences', 
            'General Academic Strand', 
            'BEEd', 
            'BSEd - English',
            'BSEd - Soc Stud', 
            'BSA', 
            'BSAIS', 
            'BSMA', 
            'BSIA', 
            'BSBA', 
            'BSBA-FM',
            'BSBA-HRDM', 
            'BSBA-MM', 
            'BSIT', 
            'BSHM',
            'Faculty'
        ]

    def get_classification_short_names(self):
        return {
            'JUNIOR HIGH SCHOOL': 'JHS',
            'Accountancy, Business and Management (ABM)': 'ABM',
            'Science, Technology, Engineering and Mathematics': 'STEM',
            'Humanities and Social Sciences': 'HUMMS',
            'General Academic Strand': 'GAS',
            'BEEd': 'BEEd',
            'BSEd - English': 'BSEd-Eng',
            'BSEd - Soc Stud': 'BSEd-SocStud',
            'BSA': 'BSA',
            'BSAIS': 'BSAIS',
            'BSMA': 'BSMA',
            'BSIA': 'BSIA',
            'BSBA': 'BSBA',
            'BSBA-FM': 'BSBA-FM',
            'BSBA-HRDM': 'BSBA-HRDM',
            'BSBA-MM': 'BSBA-MM',
            'BSIT': 'BSIT',
            'BSHM': 'BSHM',
            'Faculty': 'Faculty'
        }

    def get_vertical_courses(self):
        return [self.get_classification_short_names()[classification] 
                for classification in self.get_classifications()]

    def get_purposes_for_date(self, date):
        purposes = Attendance.objects.filter(
            time_in_date__date=date
        ).values_list('purpose', flat=True).distinct()
        return sorted(set(purpose.lower() for purpose in purposes))

    def batch_items(self, items, batch_size):
        """Split items into batches of specified size."""
        batched_items = []
        for i in range(0, len(items), batch_size):
            batched_items.append(items[i:i + batch_size])
        return batched_items

    def get_attendance_data(self, date):
        attendances = Attendance.objects.filter(
            time_in_date__date=date
        ).order_by('time_in_date')

        attendance_list = []
        course_totals = defaultdict(int)
        purpose_totals = defaultdict(int)
        total_attendance = 0

        short_names = self.get_classification_short_names()
        all_classifications = self.get_classifications()

        date_purposes = self.get_purposes_for_date(date)

        for attendance in attendances:
            classification_checks = []
            
            for classification in all_classifications:
                if classification == attendance.classification:
                    classification_checks.append('✓')
                    total_attendance += 1  # Increment total for each attendance
                else:
                    classification_checks.append('')

            attendance_dict = {
                'date': attendance.time_in_date.strftime('%b. %d, %Y'),
                'time': attendance.time_in_date.strftime('%I:%M %p').lower(),
                'name': attendance.full_name.upper(),
                'classification': classification_checks,
                'purpose': attendance.purpose.lower()
            }
            attendance_list.append(attendance_dict)

            course_short_name = short_names.get(attendance.classification, attendance.classification)
            course_totals[course_short_name] += 1
            purpose_totals[attendance.purpose.lower()] += 1

        for classification in all_classifications:
            short_name = short_names[classification]
            if short_name not in course_totals:
                course_totals[short_name] = 0

        # Convert course_totals into batched list of tuples
        course_totals_items = list(course_totals.items())
        batched_course_totals = self.batch_items(course_totals_items, 5)

        course_totals_list = []
        for classification in self.get_classifications():
            short_name = self.get_classification_short_names()[classification]
            course_totals_list.append(course_totals[short_name])

        # Calculate total purpose
        total_purpose = sum(purpose_totals.values())

        return attendance_list, batched_course_totals, dict(purpose_totals), date_purposes, total_attendance, course_totals_list, total_purpose


    def get(self, request):
        date_str = request.GET.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = timezone.now().date()

        attendance_list, batched_course_totals, purpose_totals, date_purposes, total_attendance, course_totals_list, total_purpose = self.get_attendance_data(selected_date)
    
        group_size = 25
        attendance_groups = [attendance_list[i:i + group_size] 
                        for i in range(0, len(attendance_list), group_size)]

        dynamic_purposes = {purpose: purpose_totals.get(purpose, 0) for purpose in date_purposes}

        context = {
            'attendance_groups': attendance_groups,
            'vertical_courses': self.get_vertical_courses(),
            'batched_course_totals': batched_course_totals,
            'purpose_totals': dynamic_purposes,
            'school_year': f"{selected_date.year}-{selected_date.year + 1}",
            'dynamic_date': selected_date.strftime('%B %d, %Y'),
            'uncategorized_total': dict(batched_course_totals[0]).get('Faculty', 0),
            'total_attendance': total_attendance,
            'course_totals_list': course_totals_list,
            'total_purpose': total_purpose,
        }


        # Render the template
        response = render(request, self.template_name, context)
        
        # Convert HTML to PDF
        buffer = BytesIO()
        pisa.CreatePDF(response.content, dest=buffer)
        
        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{selected_date}.pdf"'
        response.write(pdf)
        return response