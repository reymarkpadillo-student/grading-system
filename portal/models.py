from django.db import models
from django.contrib.auth.models import User

# ─── Organizational Models ────────────────────────────────────────────────────

class Department(models.Model):
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class YearLevel(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='year_levels')
    name = models.CharField(max_length=30)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['department', 'order']
        unique_together = ('department', 'name')

    def __str__(self):
        return f"{self.department.short_name or self.department.name} — {self.name}"


# ─── User / Profile ───────────────────────────────────────────────────────────

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} Profile"


# ─── Academic Term ────────────────────────────────────────────────────────────

class Semester(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class SchoolYear(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class SchoolYearSemester(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.school_year.name} - {self.semester.name}"


# ─── Curriculum ───────────────────────────────────────────────────────────────

class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Section(models.Model):
    """Represents a Block within a Year Level (e.g. BSCS 1-A)."""
    name = models.CharField(max_length=50)
    year_level = models.ForeignKey(
        YearLevel, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='blocks'
    )

    class Meta:
        ordering = ['year_level__department__name', 'year_level__order', 'name']

    def __str__(self):
        if self.year_level:
            dept = self.year_level.department.short_name or self.year_level.department.name
            return f"{dept} {self.year_level.name} — {self.name}"
        return self.name

class Period(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    position = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ─── Schedule & Grading ───────────────────────────────────────────────────────

class Schedule(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_year_semester = models.ForeignKey(SchoolYearSemester, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.subject.name} - {self.section.name}"

class Record(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='records')
    average = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.student.username} - {self.schedule}"

class GradePeriod(models.Model):
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.record} - {self.period.name}"

class GradePart(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.schedule} - {self.period.name} Part"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Excuse', 'Excuse'),
        ('Late', 'Late'),
    )
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    day_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.record} - {self.day_time} ({self.status})"

class GradingTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"Template for {self.subject.name}"

class GradingTemplateItem(models.Model):
    TYPE_CHOICES = (
        ('Quiz', 'Quiz'),
        ('Activity', 'Activity'),
        ('Exam', 'Exam'),
        ('Attendance', 'Attendance'),
    )
    grading_template = models.ForeignKey(GradingTemplate, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.grading_template} - {self.type}"

class AssessmentTypeWeight(models.Model):
    TYPE_CHOICES = (
        ('Quiz', 'Quiz'),
        ('Activity', 'Activity'),
        ('Exam', 'Exam'),
        ('Attendance', 'Attendance'),
    )
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.schedule} - {self.period.name} ({self.type})"

class Assessment(models.Model):
    grade_period = models.ForeignKey(GradePeriod, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    max_score = models.DecimalField(max_digits=6, decimal_places=2)
    date_given = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class AssessmentScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.assessment.title} - Score: {self.score}"
