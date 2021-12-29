from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import auth
from .forms import NewTrader
from .models import Trader


def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = NewTrader(request.POST)
        if form.is_valid():
            if form.match_password2():
                trader = form.save(commit=False)
                trader.init()
                trader.save()
                return redirect('login')
            else:
                messages.info(request, "Passwords don't match, try again...")
                return redirect('register')
        else:
            return render(request, "register.html", {'form': form})
    else:
        form = NewTrader()
        return render(request, "register.html", {'form': form})


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(request, username=email, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Invalid credentials')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')


@login_required
def logout(request):
    auth.logout(request)
    return redirect('index')


@login_required
def subprofile(request):
    if request.method == 'POST':
        email = request.POST['subprofile_email']
        type = request.POST['role']
        if not Trader.objects.filter(email=email).exists():
            messages.info(request, 'This profile doesn\'t exist')
            return redirect('subprofile')
        elif request.user.pk == email:
            messages.info(request, 'Choose an other profile...')
            return redirect('subprofile')
        else:
            for trader in Trader.objects.all():
                if email in trader.subprofiles['sellers'] or email in trader.subprofiles['buyers']:
                    messages.info(request, 'This profile has already been chosen as subprofile,'
                                           ' try with an other...')
                    return redirect('subprofile')

            trader = get_object_or_404(Trader, pk=request.user.pk)
            if email in trader.subprofiles['sellers']:
                messages.info(request, 'This profile is just a your seller')
                return redirect('subprofile')
            elif email in trader.subprofiles['buyers']:
                messages.info(request, 'This profile is just a your buyer')
                return redirect('subprofile')
            elif type == 'SELLER':
                trader.subprofiles['sellers'].append(email)
            else:
                trader.subprofiles['buyers'].append(email)
            trader.save()
            return render(request, 'profile.html')
    return render(request, 'subprofile.html')
