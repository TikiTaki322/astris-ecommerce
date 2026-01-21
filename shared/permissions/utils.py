def get_request_user(request):
    return getattr(request, 'user', None)


def is_authenticated(request):
    user = get_request_user(request)
    return bool(user and user.is_authenticated)


def is_backoffice_member(request):
    user = get_request_user(request)
    role = getattr(user, 'role', None)
    return bool(role and backoffice_member_check(user))


def backoffice_member_check(user):
    return bool(user.is_staff or user.role in {'seller', 'manager', 'etc'})


def is_order_owner(request, order):
    user = get_request_user(request)
    user_pk = getattr(user, 'pk', None)
    # order.user -> CustomerProfile, order.user.user -> UserProfile
    return bool(user_pk and (order.user.user_id == user_pk))