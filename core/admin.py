from django.contrib import admin

from .models import Budget, Goal, Reminder, Transaction, UserProfile


admin.site.register([UserProfile, Transaction, Budget, Goal, Reminder])
