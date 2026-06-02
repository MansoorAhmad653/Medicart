from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
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
    
    # Separate prescriptions by status
    pending_prescriptions = prescriptions.filter(status='pending')
    approved_prescriptions = prescriptions.filter(status='approved')
    rejected_prescriptions = prescriptions.filter(status='rejected')
    
    return render(request, 'prescriptions/upload.html', {
        'form': form,
        'pending_prescriptions': pending_prescriptions,
        'approved_prescriptions': approved_prescriptions,
        'rejected_prescriptions': rejected_prescriptions,
        'all_prescriptions': prescriptions,
        'prescriptions': prescriptions,
    })


@login_required
def delete_prescription(request, pk):
    """Delete a prescription file"""
    # Staff/admins can delete any prescription; regular users can only delete their own
    if request.user.is_staff or getattr(request.user, 'role', '') == 'admin':
        prescription = get_object_or_404(Prescription, pk=pk)
    else:
        prescription = get_object_or_404(Prescription, pk=pk, user=request.user)
    
    try:
        # The post_delete signal auto_delete_file_on_delete will automatically handle prescription.file.delete()
        prescription.delete()
        messages.success(request, 'Prescription deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting prescription: {str(e)}')
    
    # Redirect back to previous page if available, else to upload page
    referer = request.META.get('HTTP_REFERER')
    if referer and ('/admin/' in referer or '/dashboard/' in referer):
        return redirect(referer)
    return redirect('prescriptions:upload')



@login_required
def user_can_buy_prescription_medicine(request, medicine_id):
    """Check if user has approved prescription for a medicine"""
    from shop.models import Medicine
    medicine = get_object_or_404(Medicine, pk=medicine_id, requires_prescription=True, is_active=True)
    
    # Check if user has any approved prescription that includes this medicine
    has_approved = Prescription.objects.filter(
        user=request.user,
        status='approved',
        medicines=medicine
    ).exists()
    
    return JsonResponse({'can_buy': has_approved})


def check_prescription_status(user, medicine_id):
    """Helper function to check prescription status for a medicine"""
    prescription = Prescription.objects.filter(
        user=user,
        medicines__id=medicine_id
    ).first()
    
    if not prescription:
        return {'status': 'no_prescription', 'message': 'No prescription found'}
    
    if prescription.status == 'pending':
        return {'status': 'pending', 'message': 'Your prescription is pending approval', 'prescription': prescription}
    elif prescription.status == 'approved':
        return {'status': 'approved', 'message': 'Prescription approved!', 'prescription': prescription}
    elif prescription.status == 'rejected':
        return {'status': 'rejected', 'message': f'Prescription was rejected. Admin notes: {prescription.admin_notes}', 'prescription': prescription}
    
    return {'status': 'no_prescription', 'message': 'No valid prescription found'}
