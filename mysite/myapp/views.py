from django.shortcuts import render

# Create your views here.

def get_form(req, step):
    return render(req, f'registration/registration{step}.html')

def base_view(req):
    return render(req, 'registration/base.html')