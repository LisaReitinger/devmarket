from django.shortcuts import render

def home(request):
    return render(request, 'pages/home.html')

def custom_404(request, exception):
    return render(request, 'pages/404.html', status=404)
