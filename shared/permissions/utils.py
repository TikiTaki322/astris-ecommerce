
def get_request_user(request):
    return getattr(request, 'user', None)


def is_authenticated(request):
    user = get_request_user(request)
    return bool(user and user.is_authenticated)


def is_staff_or_seller(request):
    user = get_request_user(request)  # if not user return False
    role = getattr(user, 'role', None)
    return bool(role and (user.is_staff or role == 'seller'))


def is_order_owner(request, order):
    user = get_request_user(request)  # if not user return False
    user_id = getattr(user, 'id', None)
    # order.user -> CustomerProfile, order.user.user -> UserProfile
    return bool(user_id and (order.user.user_id == user_id))