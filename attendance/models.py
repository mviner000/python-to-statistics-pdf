import uuid
from django.db import models

class Attendance(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    school_id = models.CharField(
        max_length=50,
        help_text="School ID or Employee ID"
    )
    full_name = models.CharField(
        max_length=200
    )
    time_in_date = models.DateTimeField(
        auto_now_add=False
    )
    classification = models.CharField(
        max_length=50
    )
    purpose = models.CharField(
        max_length=50
    )

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-time_in_date']

    def __str__(self):
        return f"{self.full_name} - {self.time_in_date}"