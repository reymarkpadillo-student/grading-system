class PortalRolePermissionMixin:
    """
    Mixin to enforce role-based permissions (Superuser, Teacher, Student)
    and filter querysets in Django Admin.
    """

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
            
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.is_teacher
        model_name = self.model.__name__
        
        if is_teacher:
            # Teachers can view almost everything to perform their functions
            allowed_views = {
                'YearLevel', 'Section', 'Subject', 'Schedule', 'Record',
                'GradePeriod', 'GradePart', 'Attendance', 'GradingTemplate',
                'GradingTemplateItem', 'AssessmentTypeWeight', 'Assessment',
                'AssessmentScore', 'Period', 'User', 'UserProfile'
            }
            return model_name in allowed_views
        else:
            # Student (if given staff flag)
            allowed_views = {'Record', 'Attendance', 'GradePeriod'}
            return model_name in allowed_views

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
            
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.is_teacher
        model_name = self.model.__name__
        
        if is_teacher:
            # Teachers can add grading-related items
            allowed_adds = {
                'GradePeriod', 'Attendance', 'GradingTemplate',
                'GradingTemplateItem', 'Assessment', 'AssessmentScore'
            }
            return model_name in allowed_adds
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
            
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.is_teacher
        model_name = self.model.__name__
        
        if is_teacher:
            # Teachers can change grades, templates, and attendance
            allowed_changes = {
                'Record', 'GradePeriod', 'Attendance', 'GradingTemplate',
                'GradingTemplateItem', 'Assessment', 'AssessmentScore'
            }
            return model_name in allowed_changes
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not request.user.is_staff:
            return False
            
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.is_teacher
        model_name = self.model.__name__
        
        if is_teacher:
            # Teachers can delete grades, templates, assessments
            allowed_deletes = {
                'GradePeriod', 'Attendance', 'GradingTemplate',
                'GradingTemplateItem', 'Assessment', 'AssessmentScore'
            }
            return model_name in allowed_deletes
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
            
        is_teacher = hasattr(request.user, 'profile') and request.user.profile.is_teacher
        model_name = self.model.__name__
        
        if is_teacher:
            # Filter queryset to only return records assigned to/managed by the teacher
            if model_name == 'Subject':
                return qs.filter(user=request.user)
            elif model_name == 'Schedule':
                return qs.filter(subject__user=request.user)
            elif model_name == 'Record':
                return qs.filter(schedule__subject__user=request.user)
            elif model_name == 'GradePeriod':
                return qs.filter(record__schedule__subject__user=request.user)
            elif model_name == 'GradePart':
                return qs.filter(schedule__subject__user=request.user)
            elif model_name == 'Assessment':
                return qs.filter(grade_period__record__schedule__subject__user=request.user)
            elif model_name == 'AssessmentScore':
                # Can be filtered via assessment or direct schedule if it exists
                if hasattr(self.model, 'schedule'):
                    return qs.filter(schedule__subject__user=request.user)
                return qs.filter(assessment__grade_period__record__schedule__subject__user=request.user)
            elif model_name == 'Attendance':
                return qs.filter(record__schedule__subject__user=request.user)
            elif model_name == 'GradingTemplate':
                return qs.filter(user=request.user)
            elif model_name == 'GradingTemplateItem':
                return qs.filter(grading_template__user=request.user)
            elif model_name == 'AssessmentTypeWeight':
                return qs.filter(schedule__subject__user=request.user)
            elif model_name == 'Period':
                # Periods are system-wide settings, but only superusers can add/change them.
                # Teachers can view all periods to create assessments/templates.
                return qs
            elif model_name == 'User':
                # Autocomplete uses search on User to select students/teachers.
                # To restrict view page but allow autocomplete, we return all users
                # but hide the UserAdmin link in sidebar for non-superusers.
                return qs
        else:
            # Student view (only see own records/attendance)
            if model_name == 'Record':
                return qs.filter(student=request.user)
            elif model_name == 'GradePeriod':
                return qs.filter(record__student=request.user)
            elif model_name == 'Attendance':
                return qs.filter(record__student=request.user)
                
        return qs
