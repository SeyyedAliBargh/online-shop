import random
import string
import json
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from account.models import ShopUser
from cart.cart import Cart
from .forms import PhoneVerificationForm, OrderCreateForm
from .models import OrderItem, Order
from django.http import HttpResponse
# from coupon.models import CouponUsage
# Create your views here.



@login_required(login_url='login')
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    context = {
        'order': order,
    }
    return render(request, "order/order_detail.html", context)


def verify_phone(request):
    if request.user.is_authenticated:
        return redirect("order:order_create")
    if request.method == "POST":
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            if ShopUser.objects.filter(phone=phone).exists():
                messages.error(request, "کاربر قبلا ثبت نام شده!")
                return redirect("order:verify_phone")
            else:
                tokens = {
                    "token": "".join(random.choices("0123456789", k=5)),
                }
                request.session["verification_code"] = tokens["token"]
                request.session["phone"] = phone
                # for sending sms use below code
                # KaveSms.send_sms_with_template(phone, tokens)
                messages.success(request, "عملیات با موفقیت انجام شد")
                print("tokens:", tokens)
                return redirect("order:verify_code")

    else:
        form = PhoneVerificationForm()


    return render(request, "order/verify_phone.html", context={"form":form})


def verify_code(request):

    if request.method == "POST":
        code = request.POST.get("code")
        if code and code.isdigit():
            verification_code = request.session["verification_code"]
            phone = request.session["phone"]
            if code == verification_code:
                user = ShopUser.objects.create_user(phone=phone)
                password_characters = string.ascii_letters + string.digits + "!@#$"
                temp_password = "".join(random.choices(password_characters, k=8))
                user.set_password(temp_password)
                user.save()
                # send password to user with sms
                # tokens = {
                #     "token": temp_password,
                # }
                # KaveSms.send_sms_with_template(phone, tokens)
                print(temp_password)
                print(user)
                login(request, user)
                del request.session["verification_code"]
                del request.session["phone"]
                return redirect("order:order_create")
            else:
                messages.error(request, "کد وارد شده صحیح نمی باشد!")
    return render(request, "order/verify_code.html")


@login_required
def order_create(request):
    cart = Cart(request)
    if request.method == "POST":
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            order.buyer = request.user
            order.save()
            for item in cart:
                order_item = OrderItem.objects.create(order=order, product=item["product"],
                                                      price=item["price"], quantity=item["quantity"],
                                                      weight=item["weight"])
            # cart.clear()
            request.session["order_id"] = order.id
            print(f"form valid and session is : {dict(request.session)}")
            return redirect("order:request")
    else:
        form = OrderCreateForm()
    context = {
        "cart": cart,
        "form": form,
    }
    print(f"finish order_create and session is : {dict(request.session)}")
    return render(request, 'order/order_create.html', context)


# this part is for ZarinPall Payment

#? sandbox merchant
if settings.SANDBOX:
    sandbox = 'sandbox'
else:
    sandbox = 'www'


ZP_API_REQUEST = f"https://{sandbox}.zarinpal.com/pg/rest/WebGate/PaymentRequest.json"
ZP_API_VERIFY = f"https://{sandbox}.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
ZP_API_STARTPAY = f"https://{sandbox}.zarinpal.com/pg/StartPay/"

CallbackURL = 'http://127.0.0.1:8000/order/verify/'


def send_request(request):
    print("reqest send")
    try:
    # use try exp
        order = Order.objects.get(id=request.session["order_id"])
    except:
        return HttpResponse("error")
    cart = Cart(request)
    description = ""
    for item in order.items.all():
        description += item.product.name +", "
    data = {
        "MerchantID": settings.MERCHANT,
        "Amount": order.get_final_cost(),
        "Description": description,
        # who recive the sms ? buyer
        "Phone": request.user.phone,
        "CallbackURL": CallbackURL,
    }
    data = json.dumps(data)
    # set content length by data
    headers = {'accept': 'application/json', 'content-type': 'application/json', 'content-length': str(len(data))}
    try:
        response = requests.post(ZP_API_REQUEST, data=data, headers=headers, timeout=10)

        if response.status_code == 200:
            response_json = response.json()
            authority = response_json['Authority']
            if response_json['Status'] == 100:

                return redirect(ZP_API_STARTPAY+authority)
            else:
                return HttpResponse('Error')
        return HttpResponse('response failed')
    except requests.exceptions.Timeout:
        return HttpResponse('Timeout Error')
    except requests.exceptions.ConnectionError:
        return HttpResponse('Connection Error')


def verify(request):
    cart = Cart(request)
    order = Order.objects.get(id=request.session["order_id"])
    data = {
        "MerchantID": settings.MERCHANT,
        "Amount": order.get_final_price(),
        "Authority": request.GET.get("Authority"),
    }
    data = json.dumps(data)
    # set content length by data
    headers = {'accept': 'application/json', 'content-type': 'application/json', 'content-length': str(len(data))}
    try:
        response = requests.post(ZP_API_VERIFY, data=data, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            reference_id = response_json['RefID']
            if response_json['Status'] == 100:
                # if the user buy things in different price how many points he will get
                if cart.coupon:
                    order.coupon = cart.coupon
                    order.discount = cart.coupon.discount

                    # ثبت استفاده برای کاربر
                    usage, _ = CouponUsage.objects.get_or_create(coupon=cart.coupon, user=request.user)
                    usage.uses += 1
                    usage.save()

                    # ثبت استفاده کلی
                    order.coupon.used_count += 1
                    order.coupon.save()

                if request.user.is_authenticated:
                    if 0 < order.get_total_cost() <= 100000:
                        request.user.loyalty_points += 10
                    elif 100000 < order.get_total_cost() <= 500000:
                        request.user.loyalty_points += 20
                    elif 500000 < order.get_total_cost() <= 2000000:
                        request.user.loyalty_points += 30
                    elif 2000000 < order.get_total_cost() < 10000000:
                        request.user.loyalty_points += 40
                    elif 10000000 < order.get_total_cost():
                        request.user.loyalty_points += 60
                    else:
                        request.user.loyalty_points += 0
                request.user.save()

                for item in order.items.all():
                    item.product.inventory -= item.quantity
                    item.product.save()
                order.paid = True
                order.ref_id = reference_id
                order.save()
                return HttpResponse(f'successful , RefID: {reference_id}')
            else:
                return HttpResponse('Error')
        return HttpResponse('response failed')
    except requests.exceptions.Timeout:
        return HttpResponse('Timeout Error')
    except requests.exceptions.ConnectionError:
        return HttpResponse('Connection Error')