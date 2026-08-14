"""Companies Views"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Company


@login_required
def company_list(request):
    companies = Company.objects.filter(is_active=True)
    company_type = request.GET.get('type', '')
    search = request.GET.get('search', '')

    if company_type:
        companies = companies.filter(company_type=company_type)
    if search:
        companies = companies.filter(name__icontains=search)

    return render(request, 'companies/list.html', {
        'companies': companies,
        'company_types': Company.COMPANY_TYPE_CHOICES,
        'selected_type': company_type,
        'search': search,
    })


@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    return render(request, 'companies/detail.html', {'company': company})
