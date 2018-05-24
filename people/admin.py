# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin
from .models import User, Company


class UserAdmin(admin.ModelAdmin):
    pass


class CompanyAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Company, CompanyAdmin)
