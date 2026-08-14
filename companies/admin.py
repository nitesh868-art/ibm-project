from django.contrib import admin
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_type', 'min_package', 'max_package', 'min_cgpa')
    list_filter = ('company_type',)
    search_fields = ('name',)
