from django.shortcuts import render


def delete_session_keys(request):
    deleted_session_keys = []

    for key in dict(request.session).keys():
        print(f'Removing session key={key} | {request.session[key]}')
        del request.session[key]
        deleted_session_keys.append(key)

    if deleted_session_keys:
        request.session.modified = True

    context = {
        'session': bool(deleted_session_keys),
        'message': f'Session keys {deleted_session_keys} were deleted.' if deleted_session_keys else 'There was no session.'
    }
    return render(request, 'shared/delete_session_keys.html', context)