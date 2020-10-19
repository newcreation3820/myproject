from django.shortcuts import render,redirect
from .models import Contact
from .models import User,Product,WishList,Cart,Transaction
from django.core.mail import send_mail
import random
from django.conf import settings
import datetime
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.

@csrf_exempt
def validate_username(request):
	
	username = request.POST['username']
	data = {'is_taken': User.objects.filter(email__iexact=username).exists()}
	return JsonResponse(data)
def initiate_payment(request):
    try:
        amount = int(request.POST['amount'])
        user = User.objects.get(email=request.session['email'])
        
    except:
        return render(request, 'mycart.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=user, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://127.0.0.1:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)


def index(request):
	products=Product.objects.all()
	return render(request,'index.html',{'products':products})
def contact(request):
	if request.method=="POST":
		n=request.POST['cname']
		e=request.POST['email']
		m=request.POST['mobile']
		f=request.POST['feedback']
		Contact.objects.create(name=n,email=e,mobile=m,feedback=f)
		msg="Contact Save Successfully"
		contact=Contact.objects.all().order_by('-id')
		return render(request,'contact.html',{'msg':msg,'contact':contact})
	else:
		contact=Contact.objects.all().order_by('-id')
		return render(request,'contact.html',{'contact':contact})
def singup(request):
	if request.method=="POST":
		f=request.POST['fname']
		l=request.POST['lname']
		e=request.POST['email']
		m=request.POST['mobile']
		a=request.POST['address']
		p=request.POST['password']
		cp=request.POST['cpassword']
		ph=request.FILES['photo']
		usertype=request.POST['usertype']
		try:
			user=User.objects.get(email=e)
			msg="email Id Alredy Registered"
			return render(request,'singup.html',{'msg':msg})
		except:
			if p==cp:
				User.objects.create(fname=f,lname=l,email=e,mobile=m,address=a,password=p,cpassword=cp,photo=ph,usertype=usertype)
				rec=[e,]
				subject="OTP for Successefully Regisration"
				otp=random.randint(1000,9999)
				massege="Your OTP For Registration Is"+" "+str(otp)
				email_from=settings.EMAIL_HOST_USER
				send_mail(subject,massege,email_from,rec)
				return render(request,'otp.html',{'otp':otp,'e':e})
			else:
				msg="Password Does Not Match"
				return render(request,'singup.html',{'msg':msg})				
	else:
		return render(request,'singup.html')
def login(request):
	if request.method=="POST":
		email=request.POST['email']
		password=request.POST['password']
		usertype=request.POST['usertype']
		print(usertype)
		try:
			user=User.objects.get(email=email,password=password)
			if user.usertype=="user":
				request.session['fname']=user.fname
				request.session['email']=user.email
				request.session['imageurl']=user.photo.url
				request.session['usertype']=user.usertype
				mywishlist=WishList.objects.filter(user=user)
				request.session['total_wishlist']=len(mywishlist)
				mycart=Cart.objects.filter(user=user)
				request.session['total_cart']=len(mycart)
				products=Product.objects.all()
				return render(request,'index.html',{'products':products})
			elif user.usertype=="seller":
				request.session['fname']=user.fname
				request.session['email']=user.email
				request.session['imageurl']=user.photo.url
				request.session['usertype']=user.usertype
				return render(request,'seller_index.html')
		except:
			msg="Encorect Email or Password"
			return render(request,'login.html',{'msg':msg})
	else:
		return render(request,'login.html')      		
def shop(request):
	return render(request,'shop.html')
def logout(request):
	try:
		del request.session['fname']
		del request.session['email']
		del request.session['imageurl']
		del request.session['usertype']
		del request.session['total_wishlist']
		del request.session['total_cart']
		return render(request,'index.html')
	except:
		pass

def enter_email(request):
	if request.method=="POST":
		email=request.POST['email']
		myvar="forgot_password"

		rec=[email,]
		subject="OTP for Successefully Regisration"
		otp=random.randint(1000,9999)
		massege="Your OTP For Registration Is"+" "+str(otp)
		email_from=settings.EMAIL_HOST_USER
		send_mail(subject,massege,email_from,rec)
		return render(request,'otp.html',{'otp':otp,'e':email,'myvar':myvar})
	return render(request,'enter_email.html')
def verify_otp(request):
	myvar=""
	otp=request.POST['otp']
	email=request.POST['email']
	u_otp=request.POST['u_otp']
	try:
		if request.POST['myvar']:
			myvar=request.POST['myvar']
	except Exception as e:
		print(e)
	
	if otp==u_otp and myvar=="forgot_password":
		return render(request,'newpassword.html',{'email':email})
	elif otp==u_otp:
		user=User.objects.get(email=email)
		user.status="active"
		user.save()
		return render(request,'login.html')
	else:
		msg="Invalid OTP"
		return render(request,'otp.html',{'msg':msg,'otp':otp,'e':email})

def update_password(request):
	email=request.POST['email']
	password=request.POST['password']
	cpassword=request.POST['cpassword']
	print(email)
	print(password)
	print(cpassword)
	try:
		user=User.objects.get(email=email)
		if password==cpassword:
			user.password=password
			user.cpassword=cpassword
			user.save()
			return render(request,'login.html')
		else:
			msg="Password & Confirm Password Does Not Matched"
			return render(request,'newpassword.html',{'email':email,'msg':msg})
	except:
		pass

def change_password(request):
	if request.method=="POST":

		old_password=request.POST['old_password']
		password=request.POST['password']
		cpassword=request.POST['cpassword']

		try:
			user=User.objects.get(email=request.session['email'])
			if user.password==old_password:
				if password==cpassword:
					user.password=password
					user.cpassword=password
					user.save()
					return redirect('logout')
				elif user.usertype=="user":
					msg="Password & Confirm Password Does Not Matched"
					return render(request,'change_password.html',{'msg':msg})
				else:
					msg="Password & Confirm Password Does Not Matched"
					return render(request,'seller_change_password.html',{'msg':msg})
			elif user.usertype=="user":
				msg="Old Password Does Not Matched"
				return render(request,'change_password.html',{'msg':msg})
			else:
				msg="Old Password Does Not Matched"
				return render(request,'seller_change_password.html',{'msg':msg})
		except:
			pass

	else:
		user=User.objects.get(email=request.session['email'])
		if user.usertype=="user":
			return render(request,'change_password.html')
		else:
			return render(request,'seller_change_password.html')

def add_product(request):
	if request.method=="POST":
		product_category=request.POST['product_category']
		product_name=request.POST['product_name']
		product_price=request.POST['product_price']
		product_desc=request.POST['product_desc']
		product_photo=request.FILES['product_photo']
		Product.objects.create(product_category=product_category,product_name=product_name,product_price=product_price,product_desc=product_desc,product_photo=product_photo)
		msg="Product Added Successfully"
		return render(request,'add_product.html',{'msg':msg})
	else:
		return render(request,'add_product.html')

def seller_index(request):
	return render(request,'seller_index.html')

def view_product(request):
	products=Product.objects.all()
	return render(request,'view_product.html',{'products':products})

def product_detal(request,pk):
	data=""
	flag=True
	product=Product.objects.get(pk=pk)
	products=Product.objects.filter(product_desc__contains="shirt")
	print(products)
	try:
		user=User.objects.get(email=request.session['email'])
		wishlist=WishList.objects.filter(user=user)
		for i in wishlist:
			if i.product.pk==product.pk:
				flag=False
				break

		if user.usertype=='user':
			data="header.html"
		products=Product.objects.all()
		return render(request,'product_detail.html',{'product':product,'data':data,'flag':flag,'products':products})
	except:
		products=Product.objects.all()
		return render(request,'product_detail.html',{'product':product,'products':products})

def product_stock(request,pk):
	product=Product.objects.get(pk=pk)
	if product.product_stock=="available":
		product.product_stock="unavailable"
	else:
		product.product_stock="available"
	product.save()
	products=Product.objects.all()
	return render(request,'view_product.html',{'products':products})

def unavailable_product(request):
	products=Product.objects.filter(product_stock='unavailable')
	return render(request,'unavailable_product.html',{'products':products})

def edit_product(request,pk):
	if request.method=="POST":
		product=Product.objects.get(pk=pk)
		product.product_name=request.POST['product_name']
		product.product_price=request.POST['product_price']
		product.product_desc=request.POST['product_desc']
		try:
			if request.FILES['product_photo']:
				product.product_photo=request.FILES['product_photo']
		except:
			pass
		product.save()
		msg="Product Updated Successfully"
		products=Product.objects.all()
		return render(request,'view_product.html',{'products':products,'msg':msg})

	else:
		product=Product.objects.get(pk=pk)
		return render(request,'edit_product.html',{'product':product})

def delete_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	msg="Product Deleted Successfully"
	products=Product.objects.all()
	return render(request,'view_product.html',{'products':products,'msg':msg})

def men(request):
	men_products=Product.objects.filter(product_category='men')
	return render(request,'men_products.html',{'men_products':men_products})

def add_to_wishlist(request,pk):
	msg=""
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	all_wishlist=WishList.objects.filter(user=user)
	for i in all_wishlist:
		if product.pk==i.product.pk:
			msg="Product Is Already In Your WishList"
			mywishlist=WishList.objects.filter(user=user)
			return render(request,'mywishlist.html',{'mywishlist':mywishlist,'msg':msg})
	else:
		WishList.objects.create(user=user,product=product)
		try:
			cart=Cart.objects.get(product=product)
			cart.delete()
			msg="Product Added To Wishlist Successfully"
		except:
			pass
		mywishlist=WishList.objects.filter(user=user)
		request.session['total_wishlist']=len(mywishlist)
		mycart=Cart.objects.filter(user=user)
		request.session['total_cart']=len(mycart)
		return render(request,'mywishlist.html',{'mywishlist':mywishlist,'msg':msg})


def mywishlist(request):
	user=User.objects.get(email=request.session['email'])
	mywishlist=WishList.objects.filter(user=user)
	return render(request,'mywishlist.html',{'mywishlist':mywishlist})

def remove_wishlist(request,pk):
	user=User.objects.get(email=request.session['email'])
	wishlist=WishList.objects.get(pk=pk)
	wishlist.delete()
	msg="Product Removed From WishList Successfully"
	mywishlist=WishList.objects.filter(user=user)
	request.session['total_wishlist']=len(mywishlist)
	mycart=Cart.objects.filter(user=user)
	request.session['total_cart']=len(mycart)
	return render(request,'mywishlist.html',{'mywishlist':mywishlist,'msg':msg})

def add_to_cart(request,pk):
	total_price=0
	msg=""
	user=User.objects.get(email=request.session['email'])
	product=Product.objects.get(pk=pk)
	all_cart=Cart.objects.filter(user=user)
	for i in all_cart:
		if product.pk==i.product.pk:
			msg="Product Is Already In Your Cart"
			mycart=Cart.objects.filter(user=user)
			return render(request,'mycart.html',{'mycart':mycart,'msg':msg})
	else:
		Cart.objects.create(user=user,product=product)
		try:
			wishlist=WishList.objects.get(product=product)
			wishlist.delete()
			msg="Product Added To Cart Successfully"
		except:
			pass
		mycart=Cart.objects.filter(user=user)
		for i in mycart:
			total_price=int(total_price)+int(i.product.product_price)
		request.session['total_cart']=len(mycart)
		mywishlist=WishList.objects.filter(user=user)
		request.session['total_wishlist']=len(mywishlist)
		return render(request,'mycart.html',{'mycart':mycart,'msg':msg,'total_price':total_price})

def remove_cart(request,pk):
	total_price=0
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.get(pk=pk)
	cart.delete()
	msg="Product Removed From Cart Successfully"
	mycart=Cart.objects.filter(user=user)
	for i in mycart:
		total_price=int(total_price)+int(i.product.product_price)
	request.session['total_cart']=len(mycart)
	mywishlist=WishList.objects.filter(user=user)
	request.session['total_wishlist']=len(mywishlist)
	return render(request,'mycart.html',{'mycart':mycart,'msg':msg,'total_price':total_price})

def mycart(request):
	total_price=0
	user=User.objects.get(email=request.session['email'])
	mycart=Cart.objects.filter(user=user)
	
	for i in mycart:
		total_price=int(total_price)+int(i.product.product_price)

	return render(request,'mycart.html',{'mycart':mycart,'total_price':total_price})

def review(request,pk):
	product=Product.objects.get(pk=pk)
	if request.method=="POST":
		product.product_rating=request.POST['rating']
		product.save()
		return render(request,'product_review.html',{'product':product})
	product=Product.objects.get(pk=pk)
	return render(request,'product_review.html',{'product':product})