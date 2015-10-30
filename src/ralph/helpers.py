
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
