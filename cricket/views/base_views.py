from django.shortcuts import render
from django.http import JsonResponse

def home(request):
    """Render the homepage."""
    return render(request, 'cricket/home.html')

def clear_message_flag(request):
    """AJAX endpoint to clear message flags."""
    return JsonResponse({'status': 'success'}) 