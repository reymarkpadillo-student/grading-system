from django.shortcuts import render, redirect
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def clear_recent_actions(request):
    LogEntry.objects.all().delete()
    return redirect('admin:index')
