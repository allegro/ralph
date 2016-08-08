from django.templatetags.cache import CacheNode
from django.template import Library, TemplateSyntaxError

register = Library()


class MyCache(CacheNode):
    def __init__(self, *args, **kwargs):
        self.prefix = kwargs.pop('prefix', None)
        super().__init__(*args, **kwargs)

    def render(self, context):
        if self.prefix:
            print(self.prefix)
            self.fragment_name = '{}_{}'.format(
                self.prefix.resolve(context), self.fragment_name
            )
        return super().render(context)


@register.tag('cache_fragment')
def cache_with_dynamic_fragment_name(parser, token):
    nodelist = parser.parse(('endcache',))
    parser.delete_first_token()
    tokens = token.split_contents()
    prefix = None
    if len(tokens) < 3:
        raise TemplateSyntaxError("'%r' tag requires at least 2 arguments." % tokens[0])
    if len(tokens) > 3:
        if tokens[-1].startswith('prefix='):
            prefix = parser.compile_filter(tokens[-1][len('prefix='):])
            tokens = tokens[:-1]
    return MyCache(
        nodelist,
        parser.compile_filter(tokens[1]),
        tokens[2],
        [parser.compile_filter(t) for t in tokens[3:]],
        None,
        prefix=prefix
    )
