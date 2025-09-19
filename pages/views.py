from django.shortcuts import render

def home_view(request):
    """Home page view for testing TailwindCSS"""
    return render(request, 'base.html')
