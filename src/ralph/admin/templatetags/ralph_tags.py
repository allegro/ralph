# -*- coding: utf-8 -*-
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.contrib.admin.views.main import SEARCH_VAR
from django.template import Library

from ralph.admin.helpers import (
    get_content_type_for_model,
    get_field_by_relation_path,
    get_value_by_relation_path
)
from ralph.lib.transitions.models import TransitionsHistory

register = Library()


@register.inclusion_tag(
    "admin/templatetags/download_attachment.html", takes_context=True
)
def download_attachments(context):
    return {
        "attachments_to_download": context.request.session.pop(
            "attachments_to_download", []
        )
    }


@register.inclusion_tag("admin/templatetags/tabs.html", takes_context=True)
def views_tabs(context, views, name=None, obj=None):
    """
    Render extra views as tabs.
    """
    result = []
    if obj:
        for view in views:
            codename = "{}.{}".format(obj._meta.app_label, view.permision_codename)
            if context.request.user.has_perm(codename):
                result.append(view)
    else:
        result = views
    return {"views": result, "name": name, "object": obj}


@register.inclusion_tag("admin/search_form.html", takes_context=True)
def contextual_search_form(context, search_url, search_fields, verbose_name):
    context.update(
        {
            "search_url": search_url,
            "search_fields": search_fields,
            "search_var": SEARCH_VAR,
            "verbose_name": verbose_name.lower(),
        }
    )
    return context


@register.inclusion_tag("admin/submit_line.html", takes_context=True)
def ralph_submit_row(context):
    """
    Overriding the default templatetag Django and adding
    to it multi_add_url of context.

    Return context.
    """
    ctx = submit_row(context)
    ctx["multi_add_url"] = context.get("multi_add_url", None)
    ctx["multi_add_field"] = context.get("multi_add_field", None)
    return ctx


@register.filter
def get_attr(obj, attr):
    """
    Return class atributte.

    Example:
    {{ obj|get_attr:"my_atribute" }}

    """
    return get_value_by_relation_path(obj, attr)


@register.filter
def get_verbose_name(obj, name):
    """
    Return verbose name from Django Model.

    Example:
    {{ obj|get_verbose_name:"my_field" }}

    """
    return get_field_by_relation_path(obj, name).verbose_name


@register.inclusion_tag("admin/templatetags/transition_history.html")
def transition_history(obj):
    """
    Display transition history for model.

    Args:
        obj: Django model instance

    Example:
        {% transition_history object %}
    """
    content_type = get_content_type_for_model(obj)
    history = (
        TransitionsHistory.objects.filter(content_type=content_type, object_id=obj.pk)
        .select_related("logged_user")
        .order_by("-created")
    )

    return {"transitions_history": history, "transition_history_in_fieldset": True}
