from django.db.models import ManyToManyField


class PolymorphicManyToManyField(ManyToManyField):
    def save_form_data(self, instance, data):
        getattr(instance, self.attname).set(data[:])
