
import matplotlib.pyplot as plt
import base64
from io import BytesIO

from django.shortcuts import render
from django.views.generic import View
from django.utils import timezone
from collections import defaultdict
from django.db.models import Count
from django.db.models import Q
from datetime import datetime, time
import pandas as pd
from .models import Attendance
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse

from django.shortcuts import render
from django.views.generic import View
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.conf import settings
import os
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from collections import defaultdict
from django.utils import timezone

import calendar
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.views import View
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from collections import defaultdict
from .models import Attendance


class DailyStatisticsReportView(View):
    template_name = 'attendance_report_total_per_day.html'

    def get_time_ranges(self, target_date):
        """Generate time ranges for the day from 7 AM to 5 PM"""
        time_counts = {}
        for hour in range(7, 18):  # 7am to 5pm
            start_time = timezone.make_aware(datetime.combine(target_date, time(hour, 0)))
            end_time = timezone.make_aware(datetime.combine(target_date, time(hour + 1, 0)))
            time_str = start_time.strftime('%I:%M %p') + ' - ' + end_time.strftime('%I:%M %p')
            time_counts[time_str] = {
                'start_time': start_time,
                'end_time': end_time
            }
        return time_counts

    def get_attendance_data(self, target_date):
        # Create time range for the entire day
        start_of_day = timezone.make_aware(datetime.combine(target_date, time.min))
        end_of_day = timezone.make_aware(datetime.combine(target_date, time.max))
        
        # Get base queryset for the day
        attendance_data = Attendance.objects.filter(
            time_in_date__range=(start_of_day, end_of_day)
        )

        # Get time ranges
        time_ranges = self.get_time_ranges(target_date)
        time_counts = {}

        # Senior High School classifications
        shs_classifications = [
            'Accountancy, Business and Management (ABM)',
            'Science, Technology, Engineering and Mathematics',
            'Humanities and Social Sciences',
            'General Academic Strand'
        ]

        # Calculate counts for each time range
        for time_str, time_range in time_ranges.items():
            counts = attendance_data.filter(
                time_in_date__gte=time_range['start_time'],
                time_in_date__lt=time_range['end_time']
            ).aggregate(
                Faculty=Count('id', filter=Q(classification='Faculty')),
                Junior_High_School=Count('id', filter=Q(classification='JUNIOR HIGH SCHOOL')),
                Senior_High_School=Count('id', filter=Q(classification__in=shs_classifications)),
                College=Count('id', filter=Q(
                    classification__in=[
                        'BEEd', 'BSEd - English', 'BSEd - Soc Stud',
                        'BSA', 'BSAIS', 'BSMA', 'BSIA', 'BSBA',
                        'BSBA-FM', 'BSBA-HRDM', 'BSBA-MM', 'BSIT', 'BSHM'
                    ]
                ))
            )
            time_counts[time_str] = counts

        # Calculate totals
        total_faculty = sum(count['Faculty'] for count in time_counts.values())
        total_jhs = sum(count['Junior_High_School'] for count in time_counts.values())
        total_shs = sum(count['Senior_High_School'] for count in time_counts.values())
        total_college = sum(count['College'] for count in time_counts.values())

        return time_counts, total_faculty, total_jhs, total_shs, total_college

    def get(self, request):
        # Get date from request or use current date
        date_str = request.GET.get('date')
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()

        # Get attendance data
        time_counts, total_faculty, total_jhs, total_shs, total_college = self.get_attendance_data(target_date)

        # Prepare context
        context = {
            'time_counts': time_counts,
            'total_faculty': total_faculty,
            'total_jhs': total_jhs,
            'total_shs': total_shs,
            'total_college': total_college,
            'dynamic_date': target_date.strftime('%B %d, %Y'),
            'school_year': f"{target_date.year - 1}-{target_date.year}",
        }

        # Render to HTML
        response = render(request, self.template_name, context)
        
        # Convert to PDF
        buffer = BytesIO()
        pisa.CreatePDF(response.content, dest=buffer)
        
        # Create response
        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"daily_statistics_{target_date.strftime('%Y-%m-%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response


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
    
        group_size = 30
        attendance_groups = [attendance_list[i:i + group_size] 
                        for i in range(0, len(attendance_list), group_size)]

        dynamic_purposes = {purpose: purpose_totals.get(purpose, 0) for purpose in date_purposes}

        context = {
            'attendance_groups': attendance_groups,
            'vertical_courses': self.get_vertical_courses(),
            'batched_course_totals': batched_course_totals,
            'purpose_totals': dynamic_purposes,
            'school_year': f"{selected_date.year - 1}-{selected_date.year}",
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
    
class HourlyCourseSummaryView(View):
    template_name = 'hourly_course_summary_pdf.html'
    
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

    def get_hour_ranges(self):
        return [
            ('07:00', '08:00'), ('08:00', '09:00'),
            ('09:00', '10:00'), ('10:00', '11:00'),
            ('11:00', '12:00'), ('12:00', '13:00'),
            ('13:00', '14:00'), ('14:00', '15:00'),
            ('15:00', '16:00'), ('16:00', '17:00'),
            ('17:00', '18:00')
        ]

    def format_time_range(self, start, end):
        def convert_to_12hr(time_str):
            time_obj = datetime.strptime(time_str, '%H:%M')
            hour = int(time_obj.strftime('%I'))
            minute = time_obj.strftime('%M')
            return f"{hour}:{minute}"

        start_time = convert_to_12hr(start)
        end_time = convert_to_12hr(end)
        return f"{start_time}-{end_time}"

    def get_hourly_data(self, date):
        # Get all attendance records for the day
        attendances = Attendance.objects.filter(
            time_in_date__date=date
        ).order_by('time_in_date')

        classifications = self.get_classifications()
        grid_data = []
        column_totals = [0] * len(classifications)
        grand_total = 0

        # Process each time range
        for start_hour, end_hour in self.get_hour_ranges():
            time_key = self.format_time_range(start_hour, end_hour)
            
            # Initialize row counts
            counts = [0] * len(classifications)
            row_total = 0
            
            # Count attendances for this hour range
            start_time = datetime.strptime(start_hour, '%H:%M').time()
            end_time = datetime.strptime(end_hour, '%H:%M').time()
            
            for attendance in attendances:
                attendance_time = attendance.time_in_date.time()
                if start_time <= attendance_time < end_time:
                    try:
                        class_index = classifications.index(attendance.classification)
                        counts[class_index] += 1
                        column_totals[class_index] += 1
                        row_total += 1
                        grand_total += 1
                    except ValueError:
                        # Skip if classification not in our list
                        continue
            
            grid_data.append({
                'time_range': time_key,
                'counts': counts,
                'row_total': row_total
            })

        return grid_data, column_totals, grand_total

    def generate_pdf(self, template_path, context):
        template = get_template(template_path)
        html = template.render(context)
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            return HttpResponse(
                result.getvalue(),
                content_type='application/pdf'
            )
        return None

    def get(self, request):
        date_str = request.GET.get('date')
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return HttpResponse("Invalid date format. Use YYYY-MM-DD", status=400)
        else:
            date = timezone.now().date()
        
        grid_data, column_totals, grand_total = self.get_hourly_data(date)
        
        # Convert classifications to short names for display
        short_names = self.get_classification_short_names()
        display_classifications = [short_names[c] for c in self.get_classifications()]
        
        context = {
            'date': date.strftime('%B %d, %Y'),
            'classifications': display_classifications,
            'grid_data': grid_data,
            'column_totals': column_totals,
            'grand_total': grand_total
        }
        
        pdf = self.generate_pdf(self.template_name, context)
        if pdf:
            response = pdf
            response['Content-Disposition'] = f'attachment; filename="hourly_course_summary_{date}.pdf"'
            return response
        
        return HttpResponse("Error Rendering PDF", status=400)

class MonthlyCourseSummaryView(View):
    template_name = 'monthly_course_summary_pdf.html'

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

    def get_hour_ranges(self):
        return [
            ('07:00', '08:00'), ('08:00', '09:00'),
            ('09:00', '10:00'), ('10:00', '11:00'),
            ('11:00', '12:00'), ('12:00', '13:00'),
            ('13:00', '14:00'), ('14:00', '15:00'),
            ('15:00', '16:00'), ('16:00', '17:00'),
            ('17:00', '18:00')
        ]

    def format_time_range(self, start, end):
        def convert_to_hour(time_str):
            time_obj = datetime.strptime(time_str, '%H:%M')
            hour_12 = time_obj.strftime('%I')  # Get 12-hour format hour with leading zero
            return str(int(hour_12))  # Convert to integer and back to string to remove leading zero
        
        start_time = convert_to_hour(start)
        end_time = convert_to_hour(end)
        return f"{start_time}-{end_time}"

    def process_hourly_data(self, attendances, date):
        classifications = self.get_classifications()
        grid_data = []
        column_totals = [0] * len(classifications)
        grand_total = 0

        for start_hour, end_hour in self.get_hour_ranges():
            time_key = self.format_time_range(start_hour, end_hour)
            counts = [0] * len(classifications)
            row_total = 0

            start_time = datetime.strptime(start_hour, '%H:%M').time()
            end_time = datetime.strptime(end_hour, '%H:%M').time()

            for attendance in attendances:
                attendance_time = attendance.time_in_date.time()
                if start_time <= attendance_time < end_time:
                    try:
                        class_index = classifications.index(attendance.classification)
                        counts[class_index] += 1
                        column_totals[class_index] += 1
                        row_total += 1
                        grand_total += 1
                    except ValueError:
                        continue

            grid_data.append({
                'time_range': time_key,
                'counts': counts,
                'row_total': row_total
            })

        return grid_data, column_totals, grand_total
    
    def format_purpose_time_display(self, start_str, end_str):
        """Format time range into 12-hour format with AM/PM, removing leading zeros."""
        start = datetime.strptime(start_str, '%H:%M')
        end = datetime.strptime(end_str, '%H:%M')
        start_fmt = start.strftime('%I:%M %p').lstrip('0')
        end_fmt = end.strftime('%I:%M %p').lstrip('0')
        return f"{start_fmt} - {end_fmt}"

    def get_monthly_data(self, year, month):
        num_days = calendar.monthrange(year, month)[1]
        dates = [datetime(year, month, day).date() for day in range(1, num_days + 1)]

        start_date = dates[0]
        end_date = dates[-1]
        attendances = Attendance.objects.filter(
            time_in_date__date__gte=start_date,
            time_in_date__date__lte=end_date
        ).order_by('time_in_date')

        attendances_by_date = defaultdict(list)
        for attendance in attendances:
            date = attendance.time_in_date.date()
            attendances_by_date[date].append(attendance)

        monthly_data = []
        for date in dates:
            daily_attendances = attendances_by_date.get(date, [])
            grid_data, column_totals, grand_total = self.process_hourly_data(daily_attendances, date)
            monthly_data.append({
                'date': date.strftime('%B %d, %Y'),
                'grid_data': grid_data,
                'column_totals': column_totals,
                'grand_total': grand_total
            })

        return monthly_data, start_date, end_date  # Return the date range as well
    
    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')

        try:
            month = int(month)
            year = int(year)
            if month < 1 or month > 12:
                raise ValueError
        except (ValueError, TypeError):
            return HttpResponse("Invalid month or year parameters", status=400)

        monthly_data, start_date, end_date = self.get_monthly_data(year, month)  # Get the date range
        short_names = self.get_classification_short_names()
        display_classifications = [short_names[cls] for cls in self.get_classifications()]

        # Calculate monthly totals
        monthly_column_totals = [0] * len(self.get_classifications())
        monthly_grand_total = 0

        # NEW: Calculate time slot totals
        time_slot_totals = defaultdict(lambda: {
            'counts': [0] * len(self.get_classifications()),
            'total': 0
        })

        for day_data in monthly_data:
            # Existing totals
            for idx, total in enumerate(day_data['column_totals']):
                monthly_column_totals[idx] += total
            monthly_grand_total += day_data['grand_total']

            # NEW: Accumulate time slot totals
            for time_slot in day_data['grid_data']:
                key = time_slot['time_range']
                for i, count in enumerate(time_slot['counts']):
                    time_slot_totals[key]['counts'][i] += count
                time_slot_totals[key]['total'] += time_slot['row_total']

        # Convert time slot totals to ordered list
        ordered_time_slots = []
        for start, end in self.get_hour_ranges():
            time_key = self.format_time_range(start, end)
            if time_key in time_slot_totals:
                ordered_time_slots.append({
                    'time_range': time_key,
                    'counts': time_slot_totals[time_key]['counts'],
                    'total': time_slot_totals[time_key]['total']
                })

        # Calculate top courses
        classifications = self.get_classifications()
        short_names = self.get_classification_short_names()
        course_totals = []
        for idx, cls in enumerate(classifications):
            course_totals.append({
                'name': short_names[cls],
                'total': monthly_column_totals[idx]
            })

        sorted_course_totals = sorted(
            course_totals, 
            key=lambda x: x['total'], 
            reverse=True
        )

        # Add rank to each course
        for idx, course in enumerate(sorted_course_totals, start=1):
            course['rank'] = idx

        # Split into three columns
        total_courses = len(sorted_course_totals)
        chunk_size = (total_courses + 2) // 3  # Ceiling division
        top_courses_col1 = sorted_course_totals[:chunk_size]
        top_courses_col2 = sorted_course_totals[chunk_size:2*chunk_size]
        top_courses_col3 = sorted_course_totals[2*chunk_size:]

        # Group the monthly data into sets of 4 for 2x2 grid layout
        grouped_data = [monthly_data[i:i + 4] for i in range(0, len(monthly_data), 4)]

        # ===== NEW CODE FOR PURPOSE SUMMARY =====
        # Get all attendances for the month
        attendances = Attendance.objects.filter(
            time_in_date__date__gte=start_date,
            time_in_date__date__lte=end_date
        )

        # Collect purposes and time slot counts
        purposes = set()
        purpose_time_counts = defaultdict(lambda: defaultdict(int))
        time_ranges = self.get_hour_ranges()

        for attendance in attendances:
            purpose = attendance.purpose.strip().lower() or 'uncategorized'
            purposes.add(purpose)
            attendance_time = attendance.time_in_date.time()

            # Determine time slot
            for start_str, end_str in time_ranges:
                start = datetime.strptime(start_str, '%H:%M').time()
                end = datetime.strptime(end_str, '%H:%M').time()
                if start <= attendance_time < end:
                    time_slot = self.format_purpose_time_display(start_str, end_str)
                    purpose_time_counts[time_slot][purpose] += 1
                    break

        purposes = sorted(purposes)
        purpose_summary_rows = []
        grand_totals = defaultdict(int)

        # Build rows for each time slot
        for start_str, end_str in time_ranges:
            time_slot_display = self.format_purpose_time_display(start_str, end_str)
            counts = purpose_time_counts.get(time_slot_display, {})
            row_counts = [counts.get(purpose, 0) for purpose in purposes]
            row_total = sum(row_counts)
            
            purpose_summary_rows.append({
                'time': time_slot_display,
                'counts': row_counts,
                'total': row_total
            })
            
            # Update grand totals
            for idx, purpose in enumerate(purposes):
                grand_totals[purpose] += row_counts[idx]

        # Prepare grand total row
        grand_total_counts = [grand_totals[purpose] for purpose in purposes]
        purpose_grand_total_row = {
            'time': 'Grand Total',
            'counts': grand_total_counts,
            'total': sum(grand_total_counts)
        }

        # NEW: Purpose Rankings
        purpose_totals = []
        for idx, purpose in enumerate(purposes):
            purpose_totals.append({
                'name': purpose.title(),
                'total': grand_totals[purpose]
            })

        # Sort purpose totals by count (highest first)
        sorted_purpose_totals = sorted(
            purpose_totals,
            key=lambda x: x['total'],
            reverse=True
        )

        # Add rank to each purpose
        for idx, purpose in enumerate(sorted_purpose_totals, start=1):
            purpose['rank'] = idx

        # Split purpose rankings into three columns
        total_purposes = len(sorted_purpose_totals)
        purpose_chunk_size = (total_purposes + 2) // 3  # Ceiling division
        top_purposes_col1 = sorted_purpose_totals[:purpose_chunk_size]
        top_purposes_col2 = sorted_purpose_totals[purpose_chunk_size:2*purpose_chunk_size]
        top_purposes_col3 = sorted_purpose_totals[2*purpose_chunk_size:]

        # ===== UPDATED STACKED BAR CHART GENERATION WITH FILTERED PERCENTAGE LABELS =====
        # Prepare data for chart
        time_labels = [ts['time_range'] for ts in ordered_time_slots]
        
        # Calculate total count for each department for ranking
        department_totals = []
        for dept_idx, dept_name in enumerate(display_classifications):
            total = sum(ts['counts'][dept_idx] for ts in ordered_time_slots)
            department_totals.append({'name': dept_name, 'total': total, 'index': dept_idx})
        
        # Sort departments by total count (highest first)
        ranked_departments = sorted(department_totals, key=lambda x: x['total'], reverse=True)
        
        # Create ordered lists based on ranking
        ranked_dept_names = [dept['name'] for dept in ranked_departments]
        ranked_dept_indices = [dept['index'] for dept in ranked_departments]
        
        # Create a 2D list of values for each department in rank order
        department_values = []
        for idx in ranked_dept_indices:
            dept_values = [ts['counts'][idx] for ts in ordered_time_slots]
            department_values.append(dept_values)

        # Generate the chart
        plt.figure(figsize=(12, 8))  # Increased height from 6 to 8
        
        # Use a colormap with enough colors or create a color cycle
        from itertools import cycle
        colors = cycle(plt.cm.tab20.colors)  # tab20 has 20 colors
        
        bottom = None
        bars = []
        
        # Calculate column sums for percentage calculation
        column_sums = {}
        for i, time_label in enumerate(time_labels):
            column_sums[i] = sum(dept_values[i] for dept_values in department_values)

        # Plot each department's values as stacked bars in rank order
        for i, (dept_name, values) in enumerate(zip(ranked_dept_names, department_values)):
            color = next(colors)  # Get next color from the cycle
            if bottom is None:
                bar = plt.bar(time_labels, values, color=color, label=dept_name)
                bottom = values
            else:
                bar = plt.bar(time_labels, values, bottom=bottom, color=color, label=dept_name)
                bottom = [b + v for b, v in zip(bottom, values)]
            
            # Calculate and add percentage labels to each segment
            prev_bottom = [0] * len(values) if i == 0 else [bottom[j] - values[j] for j in range(len(values))]
            for j, (v, pb) in enumerate(zip(values, prev_bottom)):
                # Only add percentage labels if:
                # 1. The value is greater than 0
                # 2. The total count for this time slot is >= 80
                # 3. The percentage is >= 3%
                if v > 0 and column_sums[j] >= 80:  # Add check for minimum 80 counts
                    percentage = (v / column_sums[j]) * 100 if column_sums[j] > 0 else 0
                    # Only show percentages 3% and above to reduce congestion
                    if percentage >= 3:
                        # Position the label in the middle of the segment
                        y_pos = pb + v / 2
                        plt.text(j, y_pos, f"{percentage:.0f}%", ha='center', va='center', 
                                fontsize=8, fontweight='bold')
            
            bars.append(bar)
        
        # Add total numbers on top of each bar
        for i, total in enumerate(column_sums.values()):
            if total > 0:
                plt.text(i, total + 1, str(total), ha='center', va='bottom', fontsize=9)

        # Chart styling
        month_name = calendar.month_name[int(month)]
        plt.title(f'Monthly Time Slot Usage by Department ({month_name} {year})', fontsize=14, pad=20)
        plt.xlabel('Time Slots', fontsize=10)
        plt.ylabel('Total Users', fontsize=10)
        plt.xticks(rotation=45, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Add more vertical space to accommodate the percentages
        plt.subplots_adjust(bottom=0.15)
        
        # Create legend outside the plot with departments in ranked order
        plt.legend(
            bbox_to_anchor=(1, 1),
            loc='upper left',
            fontsize=11,
            title='Departments (Ranked)',
            title_fontsize=12
        )

        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Encode image for HTML
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        chart_image = f'data:image/png;base64,{image_base64}'

        context = {
            'month': datetime(year=year, month=month, day=1).strftime('%B'),
            'year': year,
            'grouped_data': grouped_data,
            'classifications': display_classifications,
            'monthly_column_totals': monthly_column_totals,
            'monthly_grand_total': monthly_grand_total,
            'time_slot_totals': ordered_time_slots,
            'sorted_course_totals': sorted_course_totals,
            'top_courses_col1': top_courses_col1,
            'top_courses_col2': top_courses_col2,
            'top_courses_col3': top_courses_col3,

            'purpose_summary_headers': purposes,
            'purpose_summary_rows': purpose_summary_rows,
            'purpose_grand_total_row': purpose_grand_total_row,
            'top_purposes_col1': top_purposes_col1,
            'top_purposes_col2': top_purposes_col2,
            'top_purposes_col3': top_purposes_col3,

            'chart_image': chart_image,
            'chart_alt_text': 'Stacked bar chart showing monthly time slot usage by department (ranked by usage)'
        }

        # Render HTML template
        html_string = render_to_string(self.template_name, context)
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf(
            stylesheets=[],
            font_config=font_config
        )
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="monthly_summary_{month}_{year}.pdf"'
        
        return response

class FilteredMonthlyCourseSummaryView(MonthlyCourseSummaryView):
    def get_monthly_data(self, year, month):
        num_days = calendar.monthrange(year, month)[1]
        dates = [datetime(year, month, day).date() for day in range(1, num_days + 1)]

        start_date = dates[0]
        end_date = dates[-1]
        attendances = Attendance.objects.filter(
            time_in_date__date__gte=start_date,
            time_in_date__date__lte=end_date
        ).order_by('time_in_date')

        attendances_by_date = defaultdict(list)
        for attendance in attendances:
            date = attendance.time_in_date.date()
            attendances_by_date[date].append(attendance)

        monthly_data = []
        for date in dates:
            daily_attendances = attendances_by_date.get(date, [])
            grid_data, column_totals, grand_total = self.process_hourly_data(daily_attendances, date)
            
            # Skip days with zero total visitors
            if grand_total > 0:
                monthly_data.append({
                    'date': date.strftime('%B %d, %Y'),
                    'grid_data': grid_data,
                    'column_totals': column_totals,
                    'grand_total': grand_total
                })

        return monthly_data, start_date, end_date  # Return the date range to match parent class