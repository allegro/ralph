import factory
from django.contrib.auth import get_user_model

from ralph.tests.models import TestManufacturer


class UserFactory(factory.Factory):
    """
    User *password* is 'ralph'.
    """

    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: "user_{}".format(n))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(group)

    @factory.lazy_attribute
    def email(self):
        return "%s@example.com" % self.username

    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.set_password("ralph")
        user.save()
        return user


class TestManufacturerFactory(factory.django.DjangoModelFactory):
    name = factory.Iterator(["Foxconn", "Brother", "Nokia", "HTC"])
    country = factory.Iterator(["Poland", "Germany", "Italy"])

    class Meta:
        model = TestManufacturer
        django_get_or_create = ["name", "country"]
