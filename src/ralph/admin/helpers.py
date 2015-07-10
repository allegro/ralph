from django.apps import apps

APP_MODELS = {model._meta.model_name: model for model in apps.get_models()}
