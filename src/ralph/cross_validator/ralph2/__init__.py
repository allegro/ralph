from django.db import models


class SoftDeletableManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(deleted=False)
        return qs


class SoftDeletable(models.Model):
    deleted = models.BooleanField()
    objects = SoftDeletableManager()

    class Meta:
        abstract = True


def generate_meta(app_label, model_name):
    class Meta:
        managed = False
        db_table = '_'.join([app_label, model_name]).lower()
    return Meta
