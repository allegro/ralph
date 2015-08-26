
def add_request_to_form(form_class, request):
    return type(form_class.__name__, (form_class,), {'_request': request})
