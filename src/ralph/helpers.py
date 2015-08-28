
def add_request_to_form(form_class, request):
    form_class._request = request
    return form_class
