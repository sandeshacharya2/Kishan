# reports/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .models import FarmerReport, CustomerReport
from .forms import FarmerReportForm, CustomerReportForm
from accounts.models import FarmerProfile, CustomerProfile

def notify_admin_of_farmer_report(report):
    """
    Sends an email to admin when a farmer report is submitted.
    """
    subject = f"New Farmer Report: {report.subject}"
    message = f"""
A new report has been submitted by farmer {report.farmer.user.get_full_name() or report.farmer.user.username}.

Category: {report.get_category_display()}
Subject: {report.subject}
Message:
{report.message}

User Email: {report.farmer.user.email}
Submitted: {report.created_at.strftime('%Y-%m-%d %H:%M')}

Manage this report in the admin panel:
https://yourdomain.com/admin/reports/farmerreport/{report.id}/
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

def notify_admin_of_customer_report(report):
    """
    Sends an email to admin when a customer report is submitted.
    """
    subject = f"New Customer Report: {report.subject}"
    message = f"""
A new report has been submitted by customer {report.customer.user.get_full_name() or report.customer.user.username}.

Category: {report.get_category_display()}
Subject: {report.subject}
Message:
{report.message}

User Email: {report.customer.user.email}
Submitted: {report.created_at.strftime('%Y-%m-%d %H:%M')}

Manage this report in the admin panel:
https://yourdomain.com/admin/reports/customerreport/{report.id}/
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )

@login_required
def submit_farmer_report(request):
    """
    View for farmers to submit reports.
    Shows success message on form page, then optionally redirects.
    """
    farmer_profile, created = FarmerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = FarmerReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.farmer = farmer_profile
            report.save()
            notify_admin_of_farmer_report(report)
            messages.success(request, "Thank you for your report. We'll review it and help you soon!")
            
            # ✅ Clear the form but keep the success message
            form = FarmerReportForm()  # New empty form
            
            # ✅ Show success message on same page with empty form
            return render(request, 'report/farmer_report_form.html', {
                'form': form,
                'show_success': True  # Flag to show success message
            })
    else:
        form = FarmerReportForm()

    return render(request, 'report/farmer_report_form.html', {
        'form': form,
        'show_success': False
    })

@login_required
def submit_customer_report(request):
    """
    View for customers to submit reports.
    Shows success message on form page, then optionally redirects.
    """
    customer_profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = CustomerReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.customer = customer_profile
            report.save()
            notify_admin_of_customer_report(report)
            messages.success(request, "Thank you for your report. We'll look into this and get back to you!")
            
            # ✅ Clear the form but keep the success message
            form = CustomerReportForm()  # New empty form
            
            # ✅ Show success message on same page with empty form
            return render(request, 'report/customer_report_form.html', {
                'form': form,
                'show_success': True  # Flag to show success message
            })
    else:
        form = CustomerReportForm()

    return render(request, 'report/customer_report_form.html', {
        'form': form,
        'show_success': False
    })