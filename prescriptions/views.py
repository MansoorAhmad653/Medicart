from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PrescriptionForm
from .models import Prescription


@login_required
def upload_prescription(request):
    prescriptions = Prescription.objects.filter(user=request.user)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, request.FILES)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.user = request.user
            prescription.save()
            messages.success(request, 'Prescription uploaded successfully! Our pharmacist will review it shortly.')
            return redirect('prescriptions:upload')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PrescriptionForm()
    return render(request, 'prescriptions/upload.html', {'form': form, 'prescriptions': prescriptions})
