"""
Admin forms(ets) and classes to handle M2M relations from both-ends perspective,
not by through table.

Formsets and admin classes defined in this module allows to attach the other
side of M2M relation as an inline to the first side (regular Django admin allow
to attach only to intermadiate/through table in M2M relation).

Notice that this feature could be used only with M2M relations without `through`
table (model).

Example:

```
# classes
class Article(models.Model):
    title = models.CharField(max_length=255)
    ...


class Author(models.Model):
    name = models.CharField(max_length=255)
    articles = models.ManyToManyField(Article)


# Django supports M2M inline only for intermediate table
# notice that only existing article could be assigned here to author
class AuthorArticlesInline(admin.TabularInline):
    model = Author.articles.through

class AuthorAdmin(admin.ModelAdmin):
    inlines = [AuthorArticlesInline]

# this module allows to create articles directly from author inline
class AuthorArticlesM2MInline(RalphTabularM2MInline):
    model = Author.articles.through

class AuthorAdmin(admin.ModelAdmin):
    inlines = [AuthorArticlesM2MInline]
```
"""

from functools import partial

from django import forms
from django.contrib.admin.utils import flatten_fieldsets, NestedObjects
from django.core.exceptions import ValidationError
from django.db import router
from django.db.models import ForeignKey
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import (
    BaseInlineFormSet,
    modelform_defines_fields,
    modelformset_factory
)
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy as _

from ralph.admin.mixins import RalphAdminForm, RalphTabularInline


class BaseInlineM2MFormset(BaseInlineFormSet):
    """
    Adjust Django's BaseInlineFormSet to cooperate with M2M relations
    """

    def __init__(self, *args, **kwargs):
        self._fk = self.fk
        # m2m is assigned by m2minlineformset_factory
        self.fk = self.m2m
        super().__init__(*args, **kwargs)
        self.fk = self._fk

    def save_new(self, form, commit=True):
        """
        Saves and returns a new model instance for the given form (single row
        from inline formset).

        Comparing to orignal `save_new`, this method saves new instance and
        add it to m2m relation.
        """
        obj = super().save_new(form, commit)
        getattr(obj, self.m2m.attname).add(self.instance)
        return obj

    @classmethod
    def get_default_prefix(cls):
        return cls.m2m.remote_field.get_accessor_name(model=cls.model).replace("+", "")

    def save_existing_objects(self, commit=True):
        """
        Comparing to original `save_existing_objects`, delete relation, not
        whole related object.
        """
        self.changed_objects = []
        self.deleted_objects = []
        if not self.initial_forms:
            return []

        saved_instances = []
        forms_to_delete = self.deleted_forms
        for form in self.initial_forms:
            obj = form.instance
            if form in forms_to_delete:
                # If the pk is None, it means that the object can't be
                # deleted again. Possible reason for this is that the
                # object was already deleted from the DB. Refs #14877.
                if obj.pk is None:
                    continue
                self.deleted_objects.append(obj)
                # DIFFERENCE HERE COMPARING TO ORIGINAL \/
                # delete m2m assignment, not whole related object
                getattr(obj, self.m2m.attname).remove(self.instance)
            elif form.has_changed():
                self.changed_objects.append((obj, form.changed_data))
                saved_instances.append(self.save_existing(form, obj, commit=commit))
                if not commit:
                    self.saved_forms.append(form)
        return saved_instances


def get_m2m(parent_model, model):
    """
    Returns ManyToManyField field.
    """
    # need to check on both sides (m2m field will be defined only in one of the
    # models)
    for rel in parent_model._meta.get_fields(include_hidden=True):
        if (
            rel.many_to_many
            and rel.auto_created
            and issubclass(rel.related_model, model)
        ):
            return rel.field

    for rel in parent_model._meta.many_to_many:
        if issubclass(rel.related_model, model):
            return rel.field


def get_foreign_key_for_m2m(parent_model, m2m):
    """
    Returns ForeignKey from ManyToManyField to intermediate table.

    Args:
        parent_model: Django model for which admin inline is created
        m2m: ManyToManyField relation instance
    """
    for field in m2m.remote_field.through._meta.fields:
        if isinstance(field, ForeignKey) and issubclass(
            parent_model, field.remote_field.model
        ):
            return field


def m2minlineformset_factory(
    parent_model,
    model,
    form=RalphAdminForm,
    formset=BaseInlineM2MFormset,
    fk_name=None,
    fields=None,
    exclude=None,
    extra=3,
    can_order=False,
    can_delete=True,
    max_num=None,
    formfield_callback=None,
    widgets=None,
    validate_max=False,
    localized_fields=None,
    labels=None,
    help_texts=None,
    error_messages=None,
    min_num=None,
    validate_min=False,
):
    """
    Creates m2m formset. This function is very similar to
    `django.forms.models.inlineformset_factory`. The only difference is m2m
    field assignment and different extraction of FK field.
    """
    # TODO: use fk_name
    m2m = get_m2m(parent_model, model)
    fk = get_foreign_key_for_m2m(parent_model, m2m)
    kwargs = {
        "form": form,
        "formfield_callback": formfield_callback,
        "formset": formset,
        "extra": extra,
        "can_delete": can_delete,
        "can_order": can_order,
        "fields": fields,
        "exclude": exclude,
        "min_num": min_num,
        "max_num": max_num,
        "widgets": widgets,
        "validate_min": validate_min,
        "validate_max": validate_max,
        "localized_fields": localized_fields,
        "labels": labels,
        "help_texts": help_texts,
        "error_messages": error_messages,
    }
    FormSet = modelformset_factory(model, **kwargs)
    FormSet.m2m = m2m
    FormSet.fk = fk
    return FormSet


class InlineM2MAdminMixin(object):
    formset = BaseInlineM2MFormset

    def get_formset(self, request, obj=None, **kwargs):
        """
        Returns a BaseInlineFormSet class for use in admin add/change views.

        The only difference here comparing to the original one is in the last
        line.
        """
        if "fields" in kwargs:
            fields = kwargs.pop("fields")
        else:
            fields = flatten_fieldsets(self.get_fieldsets(request, obj))
        excluded = self.get_exclude(request, obj)
        exclude = [] if excluded is None else list(excluded)
        exclude.extend(self.get_readonly_fields(request, obj))
        if excluded is None and hasattr(self.form, "_meta") and self.form._meta.exclude:
            # Take the custom ModelForm's Meta.exclude into account only if the
            # InlineModelAdmin doesn't define its own.
            exclude.extend(self.form._meta.exclude)
        # If exclude is an empty list we use None, since that's the actual
        # default.
        exclude = exclude or None
        can_delete = self.can_delete and self.has_delete_permission(request, obj)
        defaults = {
            "form": self.form,
            "formset": self.formset,
            "fk_name": self.fk_name,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
            "extra": self.get_extra(request, obj, **kwargs),
            "min_num": self.get_min_num(request, obj, **kwargs),
            "max_num": self.get_max_num(request, obj, **kwargs),
            "can_delete": can_delete,
        }

        defaults.update(kwargs)
        base_model_form = defaults["form"]

        class DeleteProtectedModelForm(base_model_form):
            def hand_clean_DELETE(self):
                """
                We don't validate the 'DELETE' field itself because on
                templates it's not rendered using the field information, but
                just using a generic "deletion_field" of the InlineModelAdmin.
                """
                if self.cleaned_data.get(DELETION_FIELD_NAME, False):
                    using = router.db_for_write(self._meta.model)
                    collector = NestedObjects(using=using)
                    if self.instance.pk is None:
                        return
                    collector.collect([self.instance])
                    if collector.protected:
                        objs = []
                        for p in collector.protected:
                            objs.append(
                                # Translators: Model verbose name and instance representation,
                                # suitable to be an item in a list.
                                _("%(class_name)s %(instance)s")
                                % {"class_name": p._meta.verbose_name, "instance": p}
                            )
                        params = {
                            "class_name": self._meta.model._meta.verbose_name,
                            "instance": self.instance,
                            "related_objects": get_text_list(objs, _("and")),
                        }
                        msg = _(
                            "Deleting %(class_name)s %(instance)s would require "
                            "deleting the following protected related objects: "
                            "%(related_objects)s"
                        )
                        raise ValidationError(
                            msg, code="deleting_protected", params=params
                        )

            def is_valid(self):
                result = super(DeleteProtectedModelForm, self).is_valid()
                self.hand_clean_DELETE()
                return result

        defaults["form"] = DeleteProtectedModelForm

        if defaults["fields"] is None and not modelform_defines_fields(
            defaults["form"]
        ):
            defaults["fields"] = forms.ALL_FIELDS

        # THE ONLY DIFFERENCE HERE COMPARING TO ORIGINAL \/
        # return m2minlineformset_factory instead of inlineformset_factory

        # dirty fix for through queryset being passed as self.model in init in some cases
        if hasattr(self.model._meta, "auto_created") and self.model._meta.auto_created:
            self.model = self.model._meta.auto_created

        return m2minlineformset_factory(self.parent_model, self.model, **defaults)


class RalphTabularM2MInline(InlineM2MAdminMixin, RalphTabularInline):
    template = "admin/edit_inline/tabular_m2m.html"
