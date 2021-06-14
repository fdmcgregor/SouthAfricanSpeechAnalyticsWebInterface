from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from .services import send_welcome_email_task
import requests
import os
import datetime


def register(request):

    # allow anyone to sign up
    #if True:
    if settings.DEBUG:
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST)
            profile_form = ProfileUpdateForm(request.POST)
            if form.is_valid():

                ''' Begin reCAPTCHA validation '''
                recaptcha_response = request.POST.get('g-recaptcha-response')
                data = {
                    'secret': os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY'),
                    'response': recaptcha_response
                }
                r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
                result = r.json()

                dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Info {dt}: captcha {result}")

                ''' End reCAPTCHA validation '''

                if result['success']:
                    form.save()
                    user = form.save()

                    # create profile
                    profile = profile_form.save(commit=False)
                    saved_profile = user.profile
                    saved_profile.delete_after_transcription = profile.delete_after_transcription
                    saved_profile.save()

                    # verify email
                    user.is_active = False
                    user.save()


                    send_welcome_email_task.delay(user.pk, request.get_host())
                    messages.success(request, f'Your account has been created! You please verify your email to log in.')

                    return redirect('home')
                else:
                    messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                    return redirect('login')

        else:
            form = UserRegistrationForm()
            profile_form = ProfileUpdateForm()
        return render(request, 'users/register.html', {'form': form, 'profile_form': profile_form})

    else:

        # request login
        return redirect('requestlogin')


from .forms import ContactForm 
from django.http import HttpResponse

def request_login(request):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Info {dt}: Serving login request")

    context = {'title': 'Request access to a free trial',
            'email': 'info@saigen.co.za',
            'tel': '+27 (84) 951 9002',
            'web_address': 'https://saigen.co.za'
    }
            
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ''' Begin reCAPTCHA validation '''
            recaptcha_response = request.POST.get('g-recaptcha-response')
            data = {
                'secret': os.environ.get('GOOGLE_RECAPTCHA_SECRET_KEY'),
                'response': recaptcha_response
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()

            dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Info {dt}: captcha {result}")
            ''' End reCAPTCHA validation '''

            if result['success']:
                # send email code goes here
                sender_name = form.cleaned_data['name']
                sender_email = form.cleaned_data['email']

                message = f"{sender_name} from {sender_email} has sent you a new message:\n\n{form.cleaned_data['message']}"
                print(f"Info {dt}: {message}")

                if settings.DEBUG == False:
                    receiver_list = [os.environ.get('EMAIL_USER'), os.environ.get('MANAGER_EMAIL')]
                    #receiver_list = [os.environ.get('EMAIL_USER')]
                    send_report_email(f'New Enquiry from {sender_name} at {sender_email}', message, receiver_list) 
                    
                return render(request, 'users/login_request_success.html')
            
            else:
                messages.warning(request, 'Invalid reCAPTCHA. Please try again.')
                return redirect('home')
    else:
        form = ContactForm()

    context['form'] = form
    return render(request, 'users/request_login.html', context)


def login_request_success(request):
    return render(request, 'users/login_request_success.html')


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'users/profile.html', context)


from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_report_email(title, email_body, receiver_list):
    message = Mail(
        from_email=os.environ.get('EMAIL_USER'),
        to_emails=receiver_list,
        subject=title,
        html_content=email_body)
    
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}: Trying send email contact")
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
    except Exception as e:
        print(e.message)
    
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}: Contact email sent!")
    

from .services import account_activation_token    
from django.views import View
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User

class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not account_activation_token.check_token(user, token):
                messages.warning(request, 'Account already activated')
                return redirect('login')

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()

            messages.success(request, 'Account activated successfully')
            return redirect('login')

        except Exception as e:
            dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Info {dt}: {e}")
            pass

        return redirect('login')
    
    
        
from django.shortcuts import render,redirect
from django.urls import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate,logout,login

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username,password=password)
        
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt}: Attempting login for {username}")
        
        if user:
            if user.is_active:
                login(request,user)
                
                
                if hasattr(user, 'profile'):
                    print(f"{dt}: Logging in user {username}")
                    return redirect('home')
                    
                elif hasattr(user, 'transcriber'):
                    print(f"{dt}: Transcriber login {username}")
                    return redirect('transcribe-next')
        else:
            messages.warning(request,'Username or password not correct')
            return redirect(reverse('login'))
        
                
    else:
        form = AuthenticationForm()
    return render(request,'users/login.html',{'form':form})