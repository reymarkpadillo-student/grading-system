from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .admin_permissions import PortalRolePermissionMixin

from .models import (
    YearLevel,
    UserProfile, Semester, SchoolYear, SchoolYearSemester, Subject, Section,
    Period, Schedule, Record, GradePeriod, GradePart, Attendance, GradingTemplate,
    GradingTemplateItem, AssessmentTypeWeight, Assessment, AssessmentScore
)

# ─── Site Branding ────────────────────────────────────────────────────────────

admin.site.site_header = "CSS Department Portal Administration"
admin.site.site_title  = "CSS Department Portal"
admin.site.index_title = "CSS Department Dashboard"


# ══════════════════════════════════════════════════════════════════════════════
#  TAB NAVIGATION UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _tab_url(request, **overrides):
    """Return URL string keeping current GET params with overrides applied.
    Pass None as a value to remove that key."""
    params = request.GET.copy()
    for k, v in overrides.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = str(v)
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'


def make_tab_filters(yr_field=None, blk_field=None):
    """
    Factory: returns (YrFilter, BlkFilter) SimpleListFilter classes
    for the given ORM lookup paths.  Both must be in list_filter so Django
    admin consumes 'yr', 'blk' URL params before trying to apply them
    as raw ORM filters (which would crash).
    """

    class YrTabFilter(SimpleListFilter):
        title          = 'year level'
        parameter_name = 'yr'

        def lookups(self, request, model_admin):
            qs = YearLevel.objects.all()
            return [(y.pk, y.name) for y in qs]

        def queryset(self, request, queryset):
            if self.value() and yr_field:
                return queryset.filter(**{yr_field: self.value()})

    class BlkTabFilter(SimpleListFilter):
        title          = 'block'
        parameter_name = 'blk'

        def lookups(self, request, model_admin):
            qs = Section.objects.all()
            if request.GET.get('yr'):
                qs = qs.filter(year_level_id=request.GET['yr'])
            return [(s.pk, s.name) for s in qs]

        def queryset(self, request, queryset):
            if self.value() and blk_field:
                return queryset.filter(**{blk_field: self.value()})

    return YrTabFilter, BlkTabFilter


class TabNavMixin:
    """
    Mixin: injects tab navigation context into any ModelAdmin changelist view.
    Set list_before_template in the subclass (or let this default apply).
    """
    list_before_template = 'admin/portal/tab_nav.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        yr_id   = request.GET.get('yr')
        blk_id  = request.GET.get('blk')

        active_yr   = YearLevel.objects.filter(pk=yr_id).first()    if yr_id   else None
        active_blk  = Section.objects.filter(pk=blk_id).first()     if blk_id  else None

        # Year Level row — always shown
        tab_years   = []
        all_yr_url  = _tab_url(request, yr=None, blk=None)
        for yl in YearLevel.objects.all().order_by('order'):
            tab_years.append({
                'obj':    yl,
                'url':    _tab_url(request, yr=yl.pk, blk=None),
                'active': str(yl.pk) == str(yr_id),
            })

        # Block row — shown when a year level is active
        tab_blocks  = []
        all_blk_url = _tab_url(request, blk=None)
        if active_yr:
            for sec in Section.objects.filter(year_level=active_yr).order_by('name'):
                tab_blocks.append({
                    'obj':    sec,
                    'url':    _tab_url(request, blk=sec.pk),
                    'active': str(sec.pk) == str(blk_id),
                })

        extra_context.update({
            'tab_years':    tab_years,
            'tab_blocks':   tab_blocks,
            'active_yr':    active_yr,
            'active_blk':   active_blk,
            'all_yr_url':   all_yr_url,
            'all_blk_url':  all_blk_url,
        })
        return super().changelist_view(request, extra_context=extra_context)


# ══════════════════════════════════════════════════════════════════════════════
#  USER ADMIN
# ══════════════════════════════════════════════════════════════════════════════

class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            self.fields['password'].widget = forms.Widget()
            self.fields['password'].widget.render = lambda name, value, attrs=None, renderer=None: mark_safe(
                '<div style="padding-top: 6px;">'
                '<span class="text-success"><i class="fas fa-check-circle"></i> Password securely saved.</span><br>'
                '<div class="mt-2"><a href="../password/" class="btn btn-sm btn-outline-primary">Change password</a></div>'
                '</div>'
            )
            self.fields['password'].help_text = ''


class RoleFilter(SimpleListFilter):
    title          = 'user role'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return (('admin', 'Admin'), ('teacher', 'Teacher / Faculty'), ('student', 'Student'))

    def queryset(self, request, queryset):
        if self.value() == 'admin':
            return queryset.filter(is_superuser=True)
        if self.value() == 'teacher':
            return queryset.filter(profile__is_teacher=True, is_superuser=False)
        if self.value() == 'student':
            return queryset.filter(profile__is_teacher=False, is_superuser=False)


class UserProfileInline(StackedInline):
    model             = UserProfile
    can_delete        = False
    verbose_name_plural = 'Profile'
    fk_name           = 'user'


class CustomUserAdmin(PortalRolePermissionMixin, UserAdmin, ModelAdmin):
    form             = CustomUserChangeForm
    filter_horizontal = ()
    list_filter      = ('is_active', RoleFilter)
    inlines          = (UserProfileInline,)
    fieldsets        = (
        (None,          {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Status',      {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )


admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ══════════════════════════════════════════════════════════════════════════════
#  ACADEMICS — Department → Year Level → Block
# ══════════════════════════════════════════════════════════════════════════════

# ─── Department (REMOVED) ───────────────────────────────────────────────────



# ─── Year Level ───────────────────────────────────────────────────────────────

# Filters: only yr param needed (YearLevel IS the yr entity)
_yl_Yr, _yl_Blk = make_tab_filters(
    yr_field=None,
    blk_field=None,
)


class SectionInline(TabularInline):
    model              = Section
    extra              = 1
    fields             = ('name',)
    verbose_name       = 'Block'
    verbose_name_plural = 'Blocks'


@admin.register(YearLevel)
class YearLevelAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('__str__', 'name', 'order', 'block_count', 'view_blocks_link')
    list_filter   = (_yl_Yr, _yl_Blk, 'name')
    search_fields = ('name',)
    inlines       = [SectionInline]
    autocomplete_fields = []

    def block_count(self, obj):
        return obj.blocks.count()
    block_count.short_description = 'Blocks'

    def view_blocks_link(self, obj):
        url = f'/admin/portal/section/?yr={obj.pk}'
        return mark_safe(
            f'<a href="{url}" style="font-size:.75rem; color:rgb(2,132,199);">'
            f'View Blocks →</a>'
        )
    view_blocks_link.short_description = ''


# ─── Section / Block ──────────────────────────────────────────────────────────

_sec_Yr, _sec_Blk = make_tab_filters(
    yr_field='year_level_id',
    blk_field=None,   # Section itself IS the block
)


@admin.register(Section)
class SectionAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('name', 'get_year_level', 'view_schedules_link')
    search_fields = ('name',)
    list_filter   = (_sec_Yr, _sec_Blk)
    autocomplete_fields = ['year_level']
    verbose_name        = 'Block'
    verbose_name_plural = 'Blocks'

    def get_year_level(self, obj):
        return obj.year_level.name if obj.year_level else '—'
    get_year_level.short_description = 'Year Level'
    get_year_level.admin_order_field = 'year_level__order'

    def view_schedules_link(self, obj):
        url = f'/admin/portal/schedule/?blk={obj.pk}'
        return mark_safe(
            f'<a href="{url}" style="font-size:.75rem; color:rgb(2,132,199);">'
            f'View Schedules →</a>'
        )
    view_schedules_link.short_description = ''


# ─── Subjects & Periods (no tabs needed) ──────────────────────────────────────

@admin.register(Subject)
class SubjectAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('name', 'user')
    search_fields = ('name',)


@admin.register(Period)
class PeriodAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('name', 'position', 'is_active', 'user')
    search_fields = ('name',)
    list_filter   = ('is_active',)


# ══════════════════════════════════════════════════════════════════════════════
#  SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════

_sch_Yr, _sch_Blk = make_tab_filters(
    yr_field='section__year_level_id',
    blk_field='section_id',
)


class RecordInline(TabularInline):
    model            = Record
    extra            = 1
    show_change_link = True
    fields           = ('student', 'average')
    readonly_fields  = ('average',)


class GradePartInline(TabularInline):
    model  = GradePart
    extra  = 0
    fields = ('period', 'weight')


class AssessmentTypeWeightInline(TabularInline):
    model  = AssessmentTypeWeight
    extra  = 0
    fields = ('period', 'type', 'weight')


@admin.register(Schedule)
class ScheduleAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('subject', 'get_year_level', 'section', 'school_year_semester')
    search_fields = ('subject__name', 'section__name')
    list_filter   = (_sch_Yr, _sch_Blk, 'school_year_semester')
    inlines       = [RecordInline, GradePartInline, AssessmentTypeWeightInline]
    autocomplete_fields = ['subject', 'school_year_semester', 'section']

    def get_year_level(self, obj):
        if obj.section and obj.section.year_level:
            return obj.section.year_level.name
        return '—'
    get_year_level.short_description = 'Year Level'
    get_year_level.admin_order_field = 'section__year_level__order'


# ══════════════════════════════════════════════════════════════════════════════
#  RECORDS & GRADES
# ══════════════════════════════════════════════════════════════════════════════

_rec_Yr, _rec_Blk = make_tab_filters(
    yr_field='schedule__section__year_level_id',
    blk_field='schedule__section_id',
)


class GradePeriodInline(TabularInline):
    model            = GradePeriod
    extra            = 0
    show_change_link = True
    fields           = ('period', 'grade')


@admin.register(Record)
class RecordAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('student', 'get_year_level', 'get_block', 'get_subject', 'average')
    search_fields = (
        'student__username', 'student__first_name', 'student__last_name',
        'schedule__subject__name', 'schedule__section__name',
    )
    list_filter   = (_rec_Yr, _rec_Blk, 'schedule__school_year_semester')
    inlines       = [GradePeriodInline]
    autocomplete_fields = ['student', 'schedule']

    def get_year_level(self, obj):
        sec = obj.schedule.section
        return sec.year_level.name if sec and sec.year_level else '—'
    get_year_level.short_description = 'Year Level'

    def get_block(self, obj):
        return obj.schedule.section.name if obj.schedule.section else '—'
    get_block.short_description = 'Block'

    def get_subject(self, obj):
        return obj.schedule.subject.name
    get_subject.short_description = 'Subject'


# ══════════════════════════════════════════════════════════════════════════════
#  GRADE PERIOD
# ══════════════════════════════════════════════════════════════════════════════

_gp_Yr, _gp_Blk = make_tab_filters(
    yr_field='record__schedule__section__year_level_id',
    blk_field='record__schedule__section_id',
)


class AssessmentInline(TabularInline):
    model            = Assessment
    extra            = 1
    show_change_link = True
    fields           = ('title', 'max_score', 'date_given', 'is_active')


@admin.register(GradePeriod)
class GradePeriodAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('get_student', 'get_year_level', 'get_block', 'get_subject', 'period', 'grade')
    list_filter   = (_gp_Yr, _gp_Blk, 'period')
    search_fields = ('record__student__username', 'record__schedule__subject__name')
    inlines       = [AssessmentInline]
    autocomplete_fields = ['record', 'period']

    def get_student(self, obj):
        u = obj.record.student
        return u.get_full_name() or u.username
    get_student.short_description = 'Student'

    def get_year_level(self, obj):
        sec = obj.record.schedule.section
        return sec.year_level.name if sec and sec.year_level else '—'
    get_year_level.short_description = 'Year Level'

    def get_block(self, obj):
        sec = obj.record.schedule.section
        return sec.name if sec else '—'
    get_block.short_description = 'Block'

    def get_subject(self, obj):
        return obj.record.schedule.subject.name
    get_subject.short_description = 'Subject'


# ══════════════════════════════════════════════════════════════════════════════
#  ASSESSMENT
# ══════════════════════════════════════════════════════════════════════════════

_asmnt_Yr, _asmnt_Blk = make_tab_filters(
    yr_field='grade_period__record__schedule__section__year_level_id',
    blk_field='grade_period__record__schedule__section_id',
)


class AssessmentScoreInline(TabularInline):
    model = AssessmentScore
    extra = 1


@admin.register(Assessment)
class AssessmentAdmin(PortalRolePermissionMixin, TabNavMixin, ModelAdmin):
    list_display  = ('title', 'get_year_level', 'get_block', 'max_score', 'date_given', 'is_active')
    list_filter   = (_asmnt_Yr, _asmnt_Blk, 'date_given', 'is_active')
    search_fields = ('title', 'grade_period__record__student__username')
    inlines       = [AssessmentScoreInline]
    autocomplete_fields = ['grade_period']

    def get_year_level(self, obj):
        sec = obj.grade_period.record.schedule.section
        return sec.year_level.name if sec and sec.year_level else '—'
    get_year_level.short_description = 'Year Level'

    def get_block(self, obj):
        sec = obj.grade_period.record.schedule.section
        return sec.name if sec else '—'
    get_block.short_description = 'Block'


@admin.register(AssessmentScore)
class AssessmentScoreAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('assessment', 'schedule', 'score')
    search_fields = ('assessment__title',)
    autocomplete_fields = ['assessment']


@admin.register(AssessmentTypeWeight)
class AssessmentTypeWeightAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('schedule', 'period', 'type', 'weight')
    list_filter   = ('period', 'type')
    autocomplete_fields = ['schedule', 'period']


# ══════════════════════════════════════════════════════════════════════════════
#  ATTENDANCE
# ══════════════════════════════════════════════════════════════════════════════

_att_Yr, _att_Blk = make_tab_filters(
    yr_field='record__schedule__section__year_level_id',
    blk_field='record__schedule__section_id',
)


class AttendanceSchedFilter(SimpleListFilter):
    """4th level: filter by specific schedule/course."""
    title          = 'course'
    parameter_name = 'sched'

    def lookups(self, request, model_admin):
        qs = Schedule.objects.select_related('subject', 'section')
        blk  = request.GET.get('blk')
        yr   = request.GET.get('yr')
        if blk:
            qs = qs.filter(section_id=blk)
        elif yr:
            qs = qs.filter(section__year_level_id=yr)
        return [(s.pk, s.subject.name) for s in qs.distinct()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(record__schedule_id=self.value())
        # No course selected → show nothing (prompt user via template)
        return queryset.none()


@admin.register(Attendance)
class AttendanceAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = (
        'get_student', 'day_time', 'status', 'reason',
    )
    list_filter            = (_att_Yr, _att_Blk, AttendanceSchedFilter, 'status')
    list_per_page          = 50
    show_full_result_count = False
    search_fields = (
        'record__student__username',
        'record__student__first_name',
        'record__student__last_name',
    )
    autocomplete_fields    = ['record']
    change_list_template   = 'admin/portal/attendance_changelist.html'

    # ── queryset ──────────────────────────────────────────────────────────────
    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related(
                'record__student',
                'record__schedule__subject',
                'record__schedule__section__year_level',
            )
        )

    # ── changelist_view ───────────────────────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        yr_id    = request.GET.get('yr')
        blk_id   = request.GET.get('blk')
        sched_id = request.GET.get('sched')

        active_yr    = YearLevel.objects.filter(pk=yr_id).first()     if yr_id    else None
        active_blk   = Section.objects.filter(pk=blk_id).first()      if blk_id   else None
        active_sched = Schedule.objects.select_related('subject').filter(pk=sched_id).first() \
                       if sched_id else None

        # Process POST to save attendance updates
        if request.method == 'POST' and active_sched:
            import datetime
            updated_count = 0
            for key, val in request.POST.items():
                if key.startswith('att_'):
                    # key format: att_{record_id}_{YYYY-MM-DD}
                    parts = key.split('_')
                    if len(parts) == 3:
                        _, rec_id, date_str = parts
                        if val in dict(Attendance._meta.get_field('status').choices):
                            try:
                                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                                # The day_time in DB might be midnight
                                Attendance.objects.update_or_create(
                                    record_id=rec_id,
                                    day_time__date=dt,
                                    defaults={
                                        'day_time': datetime.datetime.combine(dt, datetime.time.min),
                                        'status': val
                                    }
                                )
                                updated_count += 1
                            except ValueError:
                                pass
            if updated_count > 0:
                self.message_user(request, f"Successfully updated {updated_count} attendance records.")
            return HttpResponseRedirect(request.get_full_path())

        # Year Level tabs
        tab_years = []
        for yl in YearLevel.objects.all().order_by('order'):
            tab_years.append({
                'obj':    yl,
                'url':    _tab_url(request, yr=yl.pk, blk=None, sched=None),
                'active': str(yl.pk) == str(yr_id),
            })

        # Block tabs
        tab_blocks = []
        if active_yr:
            for sec in Section.objects.filter(year_level=active_yr).order_by('name'):
                tab_blocks.append({
                    'obj':    sec,
                    'url':    _tab_url(request, blk=sec.pk, sched=None),
                    'active': str(sec.pk) == str(blk_id),
                })

        # Course cards — shown after block is selected
        att_courses = []
        if active_blk:
            from django.db.models import Count, Q
            schedules = (
                Schedule.objects
                .filter(section=active_blk)
                .select_related('subject')
                .distinct()
            )
            for sch in schedules:
                base = Attendance.objects.filter(record__schedule=sch)
                att_courses.append({
                    'schedule': sch,
                    'subject':  sch.subject.name,
                    'present':  base.filter(status='Present').count(),
                    'absent':   base.filter(status='Absent').count(),
                    'late':     base.filter(status='Late').count(),
                    'excuse':   base.filter(status='Excuse').count(),
                    'url':      _tab_url(request, sched=sch.pk),
                    'active':   str(sch.pk) == str(sched_id),
                })

        matrix_dates = []
        matrix_students = []
        if active_sched:
            records = Record.objects.filter(schedule=active_sched).select_related('student').order_by('student__last_name', 'student__first_name')
            attendances = Attendance.objects.filter(record__schedule=active_sched).order_by('day_time')
            
            dates_set = set()
            att_map = {}
            for a in attendances:
                d = a.day_time.date()
                dates_set.add(d)
                if a.record_id not in att_map:
                    att_map[a.record_id] = {}
                att_map[a.record_id][d] = a.status
                
            matrix_dates = sorted(list(dates_set))
            
            for r in records:
                att_dict = att_map.get(r.id, {})
                statuses = []
                for dt in matrix_dates:
                    statuses.append({
                        'date_str': dt.isoformat(),
                        'status': att_dict.get(dt, 'None')
                    })
                matrix_students.append({
                    'student_name': r.student.get_full_name() or r.student.username,
                    'student_id': r.student.username,
                    'record_id': r.id,
                    'statuses': statuses
                })

        extra_context.update({
            'tab_years':    tab_years,
            'tab_blocks':   tab_blocks,
            'att_courses':  att_courses,
            'active_yr':    active_yr,
            'active_blk':   active_blk,
            'active_sched': active_sched,
            'matrix_dates': matrix_dates,
            'matrix_students': matrix_students,
            'all_yr_url':   _tab_url(request, yr=None, blk=None, sched=None),
            'all_blk_url':  _tab_url(request, blk=None, sched=None),
            'all_sched_url':_tab_url(request, sched=None),
        })
        return super().changelist_view(request, extra_context=extra_context)

    # ── list columns ──────────────────────────────────────────────────────────
    def get_student(self, obj):
        u    = obj.record.student
        name = u.get_full_name() or u.username
        return mark_safe(
            f'<span style="font-weight:600;">{name}</span>'
            f'<br><span style="font-family:monospace; font-size:.72rem; '
            f'color:rgba(255,255,255,.4);">{u.username}</span>'
        )
    get_student.short_description = 'Student'
    get_student.admin_order_field = 'record__student__last_name'


# ══════════════════════════════════════════════════════════════════════════════
#  ACADEMIC TERM SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(SchoolYear)
class SchoolYearAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('name', 'user')
    search_fields = ('name',)


@admin.register(Semester)
class SemesterAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('name', 'user')
    search_fields = ('name',)


@admin.register(SchoolYearSemester)
class SchoolYearSemesterAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('school_year', 'semester', 'is_active')
    search_fields = ('school_year__name', 'semester__name')
    list_filter   = ('is_active',)


# ══════════════════════════════════════════════════════════════════════════════
#  GRADING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

class GradingTemplateItemInline(TabularInline):
    model = GradingTemplateItem
    extra = 1


@admin.register(GradingTemplate)
class GradingTemplateAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('user', 'subject')
    inlines       = [GradingTemplateItemInline]
    search_fields = ('user__username', 'subject__name')
    autocomplete_fields = ['user', 'subject']


@admin.register(GradingTemplateItem)
class GradingTemplateItemAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display = ('grading_template', 'type', 'weight')


@admin.register(GradePart)
class GradePartAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('schedule', 'period', 'weight')
    autocomplete_fields = ['schedule', 'period']


# ══════════════════════════════════════════════════════════════════════════════
#  USER PROFILE
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(UserProfile)
class UserProfileAdmin(PortalRolePermissionMixin, ModelAdmin):
    list_display  = ('user', 'is_teacher', 'position')
    list_filter   = ('is_teacher',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
