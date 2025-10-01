"""
    Классовые вьюхи (CBV — Class Based Views)

    get_queryset() отвечает ТОЛЬКО за выборку и фильтрацию.
    get_context_data() — за добавление в контекст чего угодно (доп. параметры, формы, данные юзера и т.д.).
    get() не трогай вообще, если не хочешь полностью переписать поведение ListView.
    template_name = где отобразить
    context_object_name = как назвать в шаблоне 
"""

#
# class ProductListView(ListView):
#     model = Product
#     template_name = 'core/product_list.html'
#     context_object_name = 'products'
#
#     def get_queryset(self):
#         queryset = Product.objects.all()
#         # queryset = Product.all_objects.all()  # Include soft-deleted objects
#         return queryset.order_by('category', 'price')
#
#
# class ProductCreateView(SellerOnlyMixin, CreateView):
#     model = Product
#     form_class = ProductForm
#     template_name = 'core/product_create.html'
#     success_url = reverse_lazy('core:product_list')
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['shop'] = self.request.user.seller_profile.shop
#         return kwargs
#
#
# class ProductDetailView(DetailView):
#     model = Product
#     template_name = 'core/product_detail.html'
#     context_object_name = 'product'
#
#
# class ProductUpdateView(SellerOnlyMixin, UpdateView):
#     model = Product
#     form_class = ProductForm
#     template_name = 'core/product_update.html'
#     success_url = reverse_lazy('core:product_list')
#
#
# class ProductDeleteView(SellerOnlyMixin, DeleteView):
#     model = Product
#     template_name = 'core/product_confirm_delete.html'
#     success_url = reverse_lazy('core:product_list')

#
# class OrderItemListView(TemplateView):
#     template_name = 'core/order_item_list.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['order_item_addition'] = self.request.GET.get('order_item_addition')
#         context['order_item_deletion'] = self.request.GET.get('order_item_deletion')
#         context['message'] = self.request.GET.get('message')
#
#         if is_authenticated_user(self.request):
#             context.update(self._get_authenticated_order_context())
#         else:
#             context.update(self._get_session_order_context())
#         return context
#
#     def _get_authenticated_order_context(self):
#         context = {}
#         order = Order.objects.filter(user=self.request.user.customer_profile, status=Order.OrderStatus.PENDING).first()
#         if order:
#             service = OrderPriceSyncService(order=order)
#             context['price_diff'] = service.sync() or order.price_diff
#             order.price_diff = False
#
#             if order.items.exists():
#                 order.amount = service.get_amount()
#                 order.save(update_fields=['amount', 'price_diff'])
#                 context['order'] = order
#             else:
#                 order.delete()
#         return context
#
#     def _get_session_order_context(self):
#         context = {}
#         session_order = self.request.session.get('session_order', {})
#         if session_order:
#             service = OrderPriceSyncService(session_order=session_order)
#             context['price_diff'] = service.sync()
#             context['amount'] = service.get_amount()
#             context['session_order'] = service.session_order
#             self.request.session['session_order'] = service.session_order
#         return context
#
#
# class OrderItemCreateView(View):
#     def post(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         product.quantity -= 1
#         if is_in_stock := not bool(product.quantity < 0):
#             product.save()
#
#             if is_authenticated_user(request):
#                 order, _ = Order.objects.get_or_create(user=request.user.customer_profile, status=Order.OrderStatus.PENDING)
#                 order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
#                 if not created:
#                     order_item.quantity += 1
#                 order_item.unit_price = product.price
#                 order_item.price = Decimal(product.price * order_item.quantity)
#                 order_item.save()
#             else:
#                 pk = str(pk)
#                 session_order = request.session.get('session_order', {})
#                 session_order[pk] = session_order.get(pk, {})
#                 session_order[pk]['product_pk'] = product.pk
#                 session_order[pk]['product_name'] = product.name
#                 session_order[pk]['quantity'] = session_order[pk].get('quantity', 0) + 1
#                 session_order[pk]['unit_price'] = str(product.price)
#                 session_order[pk]['price'] = str(Decimal(product.price * session_order[pk]['quantity']))
#                 request.session['session_order'] = session_order
#
#         return redirect_with_message(
#             'core:orderitem_list',
#             order_item_addition='1' if is_in_stock else '0',
#             message='Item was added.' if is_in_stock else f'Unfortunately "{product.name}" is out of stock.'
#         )
#
#
# class OrderItemUpdateView(View):
#     pass
#
#
# class OrderItemDeleteView(View):
#     def post(self, request, pk):
#         if is_authenticated_user(request):
#             order_item = OrderItem.objects.filter(pk=pk).first()
#             if is_order_contains_item := bool(order_item):
#                 release_product_resources(order_item)  # Returning quantity of product to stock
#                 order_item.delete()
#         else:
#             session_order = request.session.get('session_order', {})
#             key = str(pk)
#             if is_order_contains_item := key in session_order:
#                 release_product_resources(session_order[key])  # Returning quantity of product to stock
#                 del session_order[key]
#                 request.session['session_order'] = session_order
#
#         return redirect_with_message(
#             'core:orderitem_list',
#             order_item_deletion='1' if is_order_contains_item else '0',
#             message='Item was removed.' if is_order_contains_item else 'Item not found in the cart.'
#         )
#
#
# def user_orders(request):
#     if request.user.role == 'seller':
#         orders = Order.objects.all().exclude(status='pending').prefetch_related('items', 'items__product').order_by('-updated_at')
#     else:
#         orders = Order.objects.filter(
#             user=request.user.customer_profile,
#             status__in=['paid', 'shipped']).prefetch_related('items', 'items__product').order_by('-updated_at')
#
#     return render(request, 'core/order_list.html', {'orders': orders})


# def order_detail(request, pk):
#     order = Order.objects.filter(pk=pk, user=request.user.customer_profile).prefetch_related('items', 'items__product').first()
#     return render(request, 'core/order_detail_FROZEN.html', {'order': order})


""" 
- Еще нужно синхронизировать цены в момент платежа, наверное, проконсультироваться с ИИ.

- Добавить расчёт суммы доставки заказы.

- Реализовать Celery: Для реально асинхронной логики используют вынесенные воркеры (Celery), 
    которые выполняют задачи в фоне, независимо от main-thread.
    его надо привязать к отправкам писем, и моменты где работают методы Django ORM как .save() and .get()
    остальное уточнить у ИИ 

- Периодическая очистка Celery таской: удалять user.email_verification_token раз в сутки (for instance)

- Реализовать Redis (брокер)

-- INFO: В своём pet-проекте использую Celery, Redis, Docker Compose — так удобнее деплоить и разносить async-задачи по воркерам

- Сделать отмену заказа (перевод order.status в CANCELLED) по прошествию определённого времени, это касается как заказа в БД
    так и сессии (можно переделать логику работы сессионной корзины на базе Redis, там должен быть механизм автоматического удаления)
    например:
    if order.created < timezone.now() - timedelta(hours=1) and not order.is_paid():
        order.status = Order.OrderStatus.CANCELLED
    UPD:
    либо ты очищаешь/удаляешь его через celery/cron по TTL (created + 30 минут),
    or wha? ahah

- сделать privacy-policy в footer`е, мб баннер о хранении кукисов
- добавить update order логику (чтоб в самой корзине можно +- удалять добавлять элементы)

- покрыть тестами middleware?

- мб добавить отправку эмейла на ивент перехода order в статус "Paid"

- Стандартизируй префиксы логов: [RESERVE], [RELEASE], [STATUS], [MAIL].

- Еще нужно синхронизировать цены в момент платежа, наверное, проконсультироваться с ИИ

- добавить срок годности на session_order — чтобы ограничить лайфтайм. можно добавлять значение lifetime прям в сессию, 
    и обновлять его если в корзину был добавлен еще один итем.
        !!! это может сделать через Redis, в нем есть механизм ограничения лайфтайма. пока подожду с этим, и при
            переводе проекта на Redis, сделаю такой апгрейд для сессий. Тоже самое касается session['pending_user'], вместо 
                создания поля в модели для трекинга момента отправки письма, можно это отслеживать через внутренний механизм Redis.
    
- добавить срок годности на order где order.status = PENDING, удалять к хуями из БД по прошествию какого-то времени 
    (а может не удалять а переводить в статус CANCELLED и хранить в БД для отчётности)
    (Пример стратегии:
        Order.status == 'draft' + created_at < now - timedelta(days=3) → удалить или архивировать.
        Django-путь: периодическая задача через Celery beat или management command по cron.)

- DONE. убрать коммент ProductImage в core/models.py, убрать коммент для рега модели в admin.py, сделать миграции и обкатать логику.

- добавить в таблицу products поле содержащее значение vatRate(НДС), налог который хоть и входит в итоговую стоимость, 
    юридически было бы хорошо явно хранить в модели.

"""
