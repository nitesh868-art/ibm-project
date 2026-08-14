"""
Companies Models — Company database for placement preparation
"""
from django.db import models


class Company(models.Model):
    """Company model with placement details."""

    COMPANY_TYPE_CHOICES = [
        ('product', 'Product Based'),
        ('service', 'Service Based'),
        ('startup', 'Startup'),
        ('mnc', 'MNC'),
        ('psu', 'PSU'),
        ('consulting', 'Consulting'),
    ]

    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='service')
    industry = models.CharField(max_length=100, blank=True)
    headquarters = models.CharField(max_length=200, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)

    # Package details
    min_package = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                       help_text='In LPA (Lakhs Per Annum)')
    max_package = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Eligibility
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.0)
    eligible_branches = models.TextField(blank=True, help_text='Comma-separated branch codes e.g. CSE,ECE,IT')
    backlogs_allowed = models.BooleanField(default=False)

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_eligible_branches(self):
        return [b.strip() for b in self.eligible_branches.split(',') if b.strip()]
