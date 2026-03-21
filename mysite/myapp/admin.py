from django.contrib import admin
from .models import User, FreelanceTask, Currency

# Register your models here.
admin.site.register(User)
admin.site.register(FreelanceTask)
admin.site.register(Currency)
