from django import template

register = template.Library()


@register.inclusion_tag('table.html')
def table(table_rows):
    """
    Template tag for TableRender class.
    """
    return {'headers': table_rows[0], 'rows': table_rows[1:]}
