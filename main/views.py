import uuid
import stripe
from datetime import date, datetime, timedelta
from django.urls import reverse_lazy
from django.conf import settings
from django.core.mail import send_mail
from django.views import generic
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from accounts.models import User
from accounts.forms import UserForm
from . import models, forms

# Create your views here.

class IndexView(generic.TemplateView):
    template_name = 'main/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['color_categories'] = models.ColorCategory.objects.all()
        context['types'] = models.Type.objects.all()
        context['sizes'] = models.Size.objects.all()
        context['airlines'] = models.Airline.objects.all()
        context['item_same_day'] = models.Item.objects.get(uuid=settings.ITEM_SAME_DAY)
        context['item_free_shipping'] = models.Item.objects.get(uuid=settings.ITEM_FREE_SHIPPING)
        context['item_all_new'] = models.Item.objects.get(uuid=settings.ITEM_ALL_NEW)
        context['items_popular'] = models.Item.objects.annotate(Count('reservation')).order_by('-reservation__count')[:3]
        context['items_reasonable'] = models.Item.objects.order_by('fee_intercept')[:3]
        return context


class ItemListView(generic.TemplateView):
    template_name = 'main/item_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = models.Item.objects.all()
        context['sizes'] = models.Size.objects.all()
        context['airlines'] = models.Airline.objects.all()
        context['types'] = models.Type.objects.all()
        context['color_categories'] = models.ColorCategory.objects.all()
        context['items_dict'] = {}

        context['items_dict']['items_popular_all'] = items.annotate(Count('reservation')).order_by('-reservation__count')
        context['items_dict']['items_reasonable_all'] = items.order_by('fee_intercept')
        context['items_dict']['items_expensive_all'] = items.order_by('-fee_intercept')

        for size in context['sizes']:
            context['items_dict']['items_popular_' + str(size.uuid)] = items.filter(size=size).annotate(Count('reservation')).order_by('-reservation__count')
            context['items_dict']['items_reasonable_' + str(size.uuid)] = items.filter(size=size).order_by('fee_intercept')
            context['items_dict']['items_expensive_' + str(size.uuid)] = items.filter(size=size).order_by('-fee_intercept')

        items_dict_all = {
            'items_popular_': context['items_dict']['items_popular_all'],
            'items_reasonable_': context['items_dict']['items_reasonable_all'],
            'items_expensive_': context['items_dict']['items_expensive_all']
        }
        for airline in context['airlines']:
            for key, value in items_dict_all.items():
                context['items_dict'][key + str(airline.uuid)] = []
                for item in value:
                    total_dimensions = item.length + item.width + item.depth
                    if total_dimensions <= airline.max_total_dimensions_carry_on:
                        context['items_dict'][key + str(airline.uuid)].append(item)
        return context


class ItemDetailView(generic.DetailView):
    model = models.Item
    template_name = 'main/item_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['airlines'] = models.Airline.objects.all()
        return context

    def post(self, request, pk):
        params = ['start_date', 'return_date']
        for param in params:
            if not request.POST.get(param):
                messages.error(request, 'お届け日と返却日を入力してください')
                return redirect('main:item_detail', pk=pk)

        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(request.POST.get('return_date'), '%Y-%m-%d')
        if start_date > return_date - timedelta(days=2) or start_date < return_date - timedelta(days=30):
            messages.error(request, 'レンタル期間は3～30日です')
            return redirect(request.META.get('main:item_detail', pk=pk))

        item = models.Item.objects.get(uuid=request.POST.get('item'))
        for reservation in item.reservation_set.all():
            if not (return_date.date() + timedelta(days=1) < reservation.start_date or reservation.return_date < start_date.date() - timedelta(days=1)):
                messages.error(request, '同じ日程で商品が予約されています\n日程を変更するか、別の商品をお探しください')
                return redirect('main:item_detail', pk=pk)

        if request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(user=request.user)
        elif 'cart' in request.session and not request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(uuid=request.session.get('cart'))
        else:
            _uuid = str(uuid.uuid4())
            new_cart = models.Cart(uuid=_uuid)
            new_cart.save()
            cart = models.Cart.objects.get(uuid=_uuid)
        request.session['cart'] = str(cart.uuid)

        reservation = models.Reservation(
            cart=cart,
            item=item,
            start_date=start_date,
            return_date=return_date,
        )
        if request.user.is_authenticated:
            reservation.user = request.user
            reservation.zip_code = request.user.zip_code
            reservation.prefecture = request.user.prefecture
            reservation.city = request.user.city
            reservation.address = request.user.address
            reservation.address_name = request.user.address_name
            reservation.address_name_kana = request.user.address_name_kana
            reservation.email = request.user.email
            reservation.gender = request.user.gender
            reservation.age_range = request.user.age_range
        reservation.save()
        return redirect('main:cart', permanent=True)


class SearchView(generic.TemplateView):
    template_name = 'main/search.html'

    def fee_calculator(self, item):

        intercept = item.fee_intercept
        coefs = item.item_fee_coef_set.order_by('starting_point')
        fee = intercept
        start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(self.request.GET.get('return_date'), '%Y-%m-%d')
        delta = return_date - start_date
        days = delta.days + 1

        for coef in coefs:
            fee_coef = coef.fee_coef
            starting_point = coef.starting_point
            end_point = coef.end_point

            if end_point:
                if days <= end_point:
                    fee += fee_coef * (days - starting_point)
                    return round(fee, -1)
                elif end_point < days:
                    fee += fee_coef * (end_point - starting_point)
            else:
                fee += fee_coef * (days - starting_point)
                return round(fee, -1)

        return round(fee, -1)

    def get(self, request):
        params = ['start_date', 'return_date']
        for param in params:
            if not request.GET.get(param):
                messages.error(request, 'お届け日と返却日を入力してください')
                return redirect(request.META.get('HTTP_REFERER', '/'))

        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(request.GET.get('return_date'), '%Y-%m-%d')
        if start_date > return_date + timedelta(days=2) or start_date < return_date - timedelta(days=29):
            messages.error(request, 'レンタル期間は3～30日です')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        return super().get(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = models.Item.objects.annotate(Count('reservation')).order_by('-reservation__count')

        start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(self.request.GET.get('return_date'), '%Y-%m-%d')
        days = (return_date - start_date).days + 1

        sizes = models.Size.objects.all()
        for size in sizes:
            min = size.min_days
            max = size.max_days
            if max:
                if min <= days < max:
                    size_recommended = size
            elif not max:
                if min <= days:
                    size_recommended = size

        items_size = items.filter(size=size_recommended)
        if items_size:
            context['items'] = items_size
        else:
            context['items'] = items

        for item in context['items']:
            for reservation in item.reservation_set.all():
                if not (return_date.date() + timedelta(days=1) < reservation.start_date or reservation.return_date < start_date.date() - timedelta(days=1)):
                    context['items'] = items.exclude(uuid=item.uuid)

        if self.request.GET.get('color_category') and self.request.GET.get('type'):
            context['items'] = context['items'].filter(
                color_category=self.request.GET.get('color_category'),
                type=self.request.GET.get('type')
            ).annotate(Count('reservation')).order_by('-reservation__count')
            if not context['items'].count():
                context['items'] = models.Item.objects.filter(
                    color_category=self.request.GET.get('color_category'),
                    type=self.request.GET.get('type')
                ).annotate(Count('reservation')).order_by('-reservation__count')
            else:
                context['items'] = models.Item.objects.filter(color_category=self.request.GET.get('color_category')).annotate(Count('reservation')).order_by('-reservation__count')
        elif self.request.GET.get('color_category') and not self.request.GET.get('type'):
            context['items'] = context['items'].filter(color_category=self.request.GET.get('color_category')).annotate(Count('reservation')).order_by('-reservation__count')
            if not context['items'].count():
                context['items'] = models.Item.objects.filter(color_category=self.request.GET.get('color_category')).annotate(Count('reservation')).order_by('-reservation__count')
        elif self.request.GET.get('type') and not self.request.GET.get('color_category'):
            context['items'] = context['items'].filter(type=self.request.GET.get('type')).annotate(Count('reservation')).order_by('-reservation__count')
            if not context['items'].count():
                context['items'] = models.Item.objects.filter(type=self.request.GET.get('type')).annotate(Count('reservation')).order_by('-reservation__count')

        context['days'], context['fee'] = [], []
        for item in context['items']:
            context['days'].append((return_date - start_date).days + 1)
            context['fee'].append(self.fee_calculator(item))
        return context

    def post(self, request):
        if request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(user=request.user)
        elif 'cart' in request.session and not request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(uuid=request.session.get('cart'))
        else:
            _uuid = str(uuid.uuid4())
            new_cart = models.Cart(uuid=_uuid)
            new_cart.save()
            cart = models.Cart.objects.get(uuid=_uuid)
        request.session['cart'] = str(cart.uuid)
        item = models.Item.objects.get(uuid=request.POST.get('item'))
        reservation = models.Reservation(
            cart=cart,
            item=item,
            start_date=request.GET.get('start_date'),
            return_date=request.GET.get('return_date'),
            item_fee=self.fee_calculator(item),
            total_fee=self.fee_calculator(item),
            postage=0,
        )
        if request.user.is_authenticated:
            reservation.user = request.user
            reservation.zip_code = request.user.zip_code
            reservation.prefecture = request.user.prefecture
            reservation.city = request.user.city
            reservation.address = request.user.address
            reservation.address_name = request.user.address_name
            reservation.address_name_kana = request.user.address_name_kana
            reservation.email = request.user.email
            reservation.gender = request.user.gender
            reservation.age_range = request.user.age_range
        reservation.save()
        return redirect('main:cart', permanent=True)


class CartView(generic.ListView):
    model = models.Reservation
    context_object_name = 'reservations'
    template_name = 'main/cart.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(user=self.request.user)
        elif 'cart' in self.request.session and not self.request.user.is_authenticated:
            cart, _ = models.Cart.objects.get_or_create(uuid=self.request.session.get('cart'))
        else:
            _uuid = str(uuid.uuid4())
            new_cart = models.Cart(uuid=_uuid)
            new_cart.save()
            cart = models.Cart.objects.get(uuid=_uuid)
        self.request.session['cart'] = str(cart.uuid)
        return models.Reservation.objects.filter(cart=cart, status=1).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = models.Region.objects.all()
        context['attachments'] = models.Attachment.objects.all()
        return context


class RentalReadyView(generic.View):

    def fee_calculator(self):
        reservation = models.Reservation.objects.get(uuid=self.request.GET.get('reservation'))
        item = reservation.item

        intercept = item.fee_intercept
        coefs = item.item_fee_coef_set.order_by('starting_point')
        fee = intercept
        start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(self.request.GET.get('return_date'), '%Y-%m-%d')
        delta = return_date - start_date
        days = delta.days + 1

        for coef in coefs:
            fee_coef = coef.fee_coef
            starting_point = coef.starting_point
            end_point = coef.end_point

            if end_point:
                if days <= end_point:
                    fee += fee_coef * (days - starting_point)
                    return round(fee, -1)
                elif end_point < days:
                    fee += fee_coef * (end_point - starting_point)
            else:
                fee += fee_coef * (days - starting_point)
                return round(fee, -1)

        return round(fee, -1)

    def get(self, request):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        return_date = datetime.strptime(request.GET.get('return_date'), '%Y-%m-%d')
        if start_date > return_date - timedelta(days=2) or start_date < return_date - timedelta(days=30):
            messages.error(request, 'レンタル期間は3～30日です')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        request.session['reservation'] = request.GET.get('reservation')
        reservation = models.Reservation.objects.get(uuid=request.GET.get('reservation'))

        reservation.start_date = start_date
        reservation.return_date = return_date
        reservation.total_fee = int(request.GET.get('total_fee'))
        reservation.item_fee = self.fee_calculator()

        if request.GET.get('warranty') == 'true':
            reservation.is_warranted = True
        elif request.GET.get('warranty') == 'false':
            reservation.is_warranted = False

        if 'region' in request.GET:
            reservation.region = models.Region.objects.get(uuid=request.GET.get('region'))

        reservation.save()
        for uuid in request.GET.getlist('attachment'):
            attachment = models.Attachment.objects.get(uuid=uuid)
            models.ReservedAttachment.objects.get_or_create(reservation=reservation, attachment=attachment)
        for attachment in reservation.attachments.all():
            if str(attachment.uuid) not in request.GET.getlist('attachment'):
                reserved_attachment = models.ReservedAttachment.objects.get(reservation=reservation, attachment=attachment)
                reserved_attachment.delete()

        return redirect('main:rental', permanent=True)


class RentalView(generic.UpdateView):
    model = models.Reservation
    form_class = forms.RentalForm
    template_name = 'main/rental.html'
    success_url = reverse_lazy('main:rental_confirm')

    def get_object(self, queryset=None):
        obj = get_object_or_404(models.Reservation, uuid=self.request.session.get('reservation'), status=1)
        return obj


class RentalConfirmView(generic.TemplateView):
    template_name = 'main/rental_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = get_object_or_404(models.Reservation, uuid=self.request.session.get('reservation'), status=1)
        context['reservation'] = reservation
        context['days'] = (reservation.return_date - reservation.start_date).days + 1
        context['tax'] = int(round(reservation.total_fee * 0.08, -1))
        context['attachment_fee'] = 0
        for attachment in context['reservation'].attachments.all():
            context['attachment_fee'] += attachment.fee
        return context


class RentalCheckoutView(generic.View):

    def post(self, request):
        reservation = get_object_or_404(models.Reservation, uuid=self.request.session.get('reservation'), status=1)

        stripe.api_key = settings.STRIPE_API_KEY
        token = request.POST.get('stripeToken')
        charge = stripe.Charge.create(
            amount=reservation.total_fee,
            currency='jpy',
            description='支払い',
            source=token,
        )

        reservation.status = 0
        reservation.save()
        if request.user.is_authenticated:
            request.user.zip_code = reservation.zip_code
            request.user.prefecture = reservation.prefecture
            request.user.city = reservation.city
            request.user.address = reservation.address
            request.user.address_name = reservation.address_name
            request.user.address_name_kana = reservation.address_name_kana
            request.user.gender = reservation.gender
            request.user.age_range = reservation.age_range
            request.user.save()
        return redirect('main:rental_complete', permanent=True)


class RentalCompleteView(generic.CreateView):
    model = User
    form_class = UserForm
    template_name = 'main/rental_complete.html'
    success_url = reverse_lazy('accounts:complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation'] = get_object_or_404(models.Reservation, uuid=self.request.session.get('reservation'), status=0)
        if self.request.user.is_authenticated:
            del self.request.session['reservation']
        return context

    def form_valid(self, form):
        form.instance.password = make_password(self.request.POST.get('password'))
        _uuid = str(uuid.uuid4())
        user = form.save(commit=False)
        user.uuid = _uuid
        if 'reservation' in self.request.session:
            try:
                reservation = models.Reservation.objects.get(uuid=self.request.session.get('reservation'))
            except models.Reservation.DoesNotExist:
                user.save()
            else:
                user.zip_code = reservation.zip_code
                user.prefecture = reservation.prefecture
                user.city = reservation.city
                user.address = reservation.address
                user.address_name = reservation.address_name
                user.address_name_kana = reservation.address_name_kana
                user.gender = reservation.gender
                user.age_range = reservation.age_range
                user.save()
                user_saved = User.objects.get(uuid=_uuid)
                reservation.user = user_saved
                reservation.save()
            del self.request.session['reservation']

        if 'cart' in self.request.session:
            try:
                cart = models.Cart.objects.get(uuid=self.request.session.get('cart'))
            except models.Cart.DoesNotExist:
                pass
            else:
                cart.user = user
                cart.save()

        protocol = 'https://' if self.request.is_secure() else 'http://'
        host_name = settings.HOST_NAME
        send_mail(
            u'会員登録完了',
            u'会員登録が完了しました。\n' +
            '以下のURLより、メールアドレスの認証を行ってください。\n\n' +
            protocol + host_name + str(reverse_lazy('accounts:activate', args=[user.uuid,])),
            'info@anybirth.co.jp',
            [user.email],
            fail_silently=False,
        )
        return super().form_valid(form)


class RentalCompleteSocialView(generic.View):

    def get(self, request):
        user = request.user
        if 'reservation' in self.request.session:
            try:
                reservation = models.Reservation.objects.get(uuid=request.session.get('reservation'))
            except models.Reservation.DoesNotExist:
                pass
            else:
                try:
                    cart = models.Cart.objects.get(user=request.user)
                except models.Cart.DoesNotExist:
                    pass
                else:
                    reservation.cart = cart
                    request.session['cart'] = str(cart.uuid)
                reservation.user = user
                reservation.save()
                request.user.zip_code = reservation.zip_code
                request.user.prefecture = reservation.prefecture
                request.user.city = reservation.city
                request.user.address = reservation.address
                request.user.address_name = reservation.address_name
                request.user.address_name_kana = reservation.address_name_kana
                request.user.gender = reservation.gender
                request.user.age_range = reservation.age_range
                request.user.save()
            del request.session['reservation']

        if 'cart' in request.session:
            try:
                _ = models.Cart.objects.get(user=request.user)
            except models.Cart.DoesNotExist:
                try:
                    cart = models.Cart.objects.get(uuid=request.session.get('cart'))
                except models.Cart.DoesNotExist:
                    pass
                else:
                    cart.user = request.user
                    cart.save()
        return redirect('accounts:signup_social', permanent=True)
