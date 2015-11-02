# FAQ

## I've got `ImproperlyConfigured` error after attaching extra view to admin class

Single extra view class **CANNOT** be reused in multiple admin sites. To use it in multiple admin sites create separated class of extra view:

```django
class MyView(RalphDetailViewAdmin):
    icon = 'chain'
    ...

class MyView2(MyView):
    pass
```

Then use it in your admin:

```django
@register(MyModel)
class MyAdmin(RalphAdmin):
    change_views = [MyView]

@register(MyModel2)
class MyAdmin2(RalphAdmin):
    change_views = [MyView2]
```

Attachments app is an example usage of this mechanism - for every admin site that
uses `AttachmentsMixin`, there is created separated class of `AttachmentsView`.
