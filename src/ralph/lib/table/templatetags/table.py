from django import template

register = template.Library()


@register.inclusion_tag('table.html', takes_context=True)
def table(context, table_rows):
    """
    Template tag for TableRender class.
    """
    return {
        'headers': table_rows[0],
        'rows': table_rows[1:],
        'show_header': context.get('show_header', True)
    }
