from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Trader
from .models import Order
from .forms import NewOrder
from .utils import is_valid_transaction, transaction, assess_transaction, is_valid_action, get_subprofiles
from bson import ObjectId


@login_required
def orders(request):
    orders = Order.objects.exclude(trader_id=request.user.pk).filter(active__in=[True]).order_by('-timestamp')
    return render(request, "orders_list.html", {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=ObjectId(pk))

    return render(request, "order_detail.html", {'order': order})


@login_required
def order_new(request):
    if request.method == 'POST':
        form = NewOrder(request.POST)
        if form.is_valid():
            trader = form.cleaned_data['trader']
            order_btc = form.cleaned_data['btc']
            order_price = form.cleaned_data['price']
            order_type = form.cleaned_data['type']
            if is_valid_action(request.user.pk, trader.pk, order_type):
                if is_valid_transaction(trader, order_btc, order_price, order_type):
                    order = form.save(commit=False)
                    order.trader = trader
                    if order_type == 'S':
                        trader.fungible_btc -= order_btc
                    else:
                        trader.fungible_balance -= order_price
                    trader.n_open_orders += 1
                    order.save()
                    if order.type == 'P':
                        transaction(trader, order)
                    trader.save()
                    return redirect('orders')
                else:
                    profiles = get_subprofiles(request)
                    messages.info(request, "Invalid order, you couldn't have enough fungible bitcoins or balance")
                    return render(request, "order_new.html", {'form': form, 'profiles': profiles, 'new': True})
            else:
                profiles = get_subprofiles(request)
                messages.info(request, "This action is not permitted as subprofile, "
                                       "try checking if you are a seller or a buyer...")
                return render(request, "order_new.html", {'form': form, 'profiles': profiles, 'new': True})
        else:
            profiles = get_subprofiles(request)
            return render(request, "order_new.html", {'form': form, 'profiles': profiles, 'new': True})

    else:
        profiles = get_subprofiles(request)
        form = NewOrder()
        return render(request, "order_new.html", {'form': form, 'profiles': profiles, 'new': True})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=ObjectId(pk))
    old_order_btc = order.btc
    old_order_price = order.price
    old_order_type = order.type
    if request.user.pk == order.trader_id:
        if request.method == 'POST':
            form = NewOrder(request.POST, instance=order)
            if form.is_valid():
                trader = get_object_or_404(Trader, pk=request.user.pk)

                # cancel old order
                if old_order_type == order.type == 'S':
                    trader.fungible_btc += old_order_btc
                elif old_order_type == order.type == 'P':
                    trader.fungible_balance += old_order_price
                elif old_order_type != order.type:
                    if old_order_type == 'S':
                        trader.fungible_btc += old_order_btc
                    else:
                        trader.fungible_balance += old_order_price
                else:
                    print("Something went wrong...")

                # new order
                order_btc = form.cleaned_data['btc']
                order_price = form.cleaned_data['price']
                order_type = form.cleaned_data['type']
                if is_valid_transaction(trader, order_btc, order_price, order_type):
                    order = form.save(commit=False)
                    order.trader = trader
                    if order_type == 'S':
                        trader.fungible_btc -= order_btc
                    else:
                        trader.fungible_balance -= order_price
                    order.save()
                    if order.type == 'P':
                        transaction(trader, order)
                    trader.save()
                    return redirect('orders')
            else:
                return render(request, 'order_new.html', {'form': form, 'new': False})
        else:
            form = NewOrder(instance=order)
            return render(request, 'order_new.html', {'form': form, 'new': False})
    else:
        return redirect('index')


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=ObjectId(pk))
    old_order_btc = order.btc
    old_order_price = order.price
    old_order_type = order.type

    if request.user.pk == order.trader_id:

        trader = get_object_or_404(Trader, pk=request.user.pk)

        if old_order_type == 'S':
            trader.fungible_btc += old_order_btc
        else:
            trader.fungible_balance += old_order_price

        trader.n_open_orders -= 1

        trader.save()
        order.delete()
        return redirect('profile', pk=trader.pk)
    else:
        return redirect('index')


@login_required
def profile(request, pk):
    trader = request.user
    if trader.pk == pk:
        orders = Order.objects.filter(trader_id=trader.pk).exclude(active__in=[False])
        return render(request, "profile.html", {'orders': orders})
    else:
        return redirect('index')


@login_required
def info(request):
    traders = Trader.objects.all()
    result = {}
    for trader in traders:
        result[str(trader.pk)] = []
        for transaction in trader.transactions:
            timestamp = str(transaction['trans_timestamp'])
            result[str(trader.pk)].append({timestamp: assess_transaction(transaction, trader.pk)})

    return JsonResponse(result)
