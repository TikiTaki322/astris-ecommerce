
# Ctrl + Alt + O - удалить неиспользуемые импорты
# Ctrl + Alt + L - отформатировать блок приведя к PEP8

"""
CURRENTLY:

DONE - Добавить расчёт суммы доставки заказа.

- Реализовать Celery: Для реально асинхронной логики используют вынесенные воркеры (Celery), 
    которые выполняют задачи в фоне, независимо от main-thread.
    его надо привязать к отправкам писем.
    * И возможно места где отрабатывают методы Django ORM как .save() and .get()

DONE - Периодическая очистка Celery таской: удалять user.verification_token раз в сутки.
    UPD 10.12.25: зачем это делать? бред написал?
    UPD 14.01.26 реализовал очистку через метод модели eliminate_verification_token()

DONE - добавить срок годности на session_order чтобы ограничить лайфтайм. можно добавлять значение lifetime прям в сессию,
    и обновлять его если в корзину был добавлен еще один итем.
        !!! это может сделать через Redis, в нем есть механизм ограничения лайфтайма. пока подожду с этим, и при
            переводе проекта на Redis, сделаю такой апгрейд для сессий. Тоже самое касается session['pending_user']

DONE - добавить срок годности на order где order.status = PENDING, удалять к хуями из БД по прошествию какого-то времени
    (а может не удалять а переводить в статус CANCELLED/EXPIRED и хранить в БД для отчётности)
    (Пример стратегии:
        Order.status == 'draft' + created_at < now - timedelta(days=3) → удалить или архивировать.
        Django-путь: периодическая задача через Celery beat или management command по cron.)

DONE - Сделать отмену заказа (перевод order.status в CANCELLED) по прошествию определённого времени, это касается как заказа в БД
    так и сессии (можно переделать логику работы сессионной корзины на базе Redis, там должен быть механизм автоматического удаления)
    например:
    if order.created < timezone.now() - timedelta(hours=1) and not order.is_paid():
        order.status = OrderStatus.CANCELLED
    UPD:
    либо ты очищаешь/удаляешь его через celery/cron по TTL (created + 30 минут),

DONE - Нужно синхронизировать цены в момент платежа


MAYBE:

- добавить отправку эмейла на триггер смены order.status == "Paid"

- Добавить Crypto как способ оплаты, подключение к бирже через API

- добавить update order логику (чтоб в самой корзине можно +- удалять добавлять элементы)

- добавить в таблицу products поле содержащее значение vatRate(НДС), налог который хоть и входит в итоговую стоимость,
    юридически было бы хорошо явно хранить в модели.

- покрыть тестами middleware?



ABSOLUTELY BUT LATER:

- Have to implement JWT or OAuth

DONE - bug with product name on the main page (for mobile), if it longer than usual the card goes crazy, have to do fixed space for product_name

DONE - mb I have to remove user.username at all. if I use user.email for Log in, maybe username is an excess entity.

- have to test OrderListView, I've set up new QuerySet logic. I need to test the efficiency with debug_toolbar/silk

- have to test accounts/utils.py, I wrote new branch for invalidating session form cache (it triggers after password changing)

DONE - Создать чёткую структуру логгирования.
    сейчас всё сваливается в один файл с префиксом [INFO] - что никуда не годится.

- покрыть тестами основные инфранструктурные узлы
    (делать в конце, когда структура больше не будет меняться)

DONE - просмотреть ВСЕ формы, для мобилок поля ввода ужасные (не считая формы по create/update product)

- сделать человеческий HEADER, добавить лого сайта и наверное значок корзины.

- посмотреть еще раз шаблоны для рассылок

- сделать privacy-policy в footer`е, мб баннер о хранении кукисов

- подключить Sentry для кэтча ошибок/аналитики (для прода)

"""