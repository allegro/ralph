from django.http import HttpResponse


def add_request_to_form(form_class, request):
    form_class._request = request
    return form_class


def get_model_view_url_name(model, view_name, with_admin_namespace=True):
    """
    Return url name for model additional view (site). Example:
    >>> get_model_view_url_name(DataCenterAsset, 'attachment')
    'admin:data_center_datacenterasset_attachment'
    """
    params = model._meta.app_label, model._meta.model_name
    url = '{}_{}_{view_name}'.format(*params, view_name=view_name)
    if with_admin_namespace:
        url = 'admin:' + url
    return url


def generate_pdf_response(pdf_data, file_name):
    """
    Return file response for pdf file with provided content and file name
    after download.
    """
    # TODO: unify with attachments
    response = HttpResponse(
        content=pdf_data, content_type='application/pdf',
    )
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(
        file_name,
    )
    return response
