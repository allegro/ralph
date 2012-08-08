import cStringIO as StringIO
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse

from ralph.util import csvutil
from ralph.cmdb.views import BaseCMDBView, _get_pages


ROWS_PER_PAGE=20

class PaginatedView(BaseCMDBView):
    exporting_csv_file = False
    def get_context_data(self, **kwargs):
        ret = super(PaginatedView, self).get_context_data(**kwargs)
        ret.update({
            'page': self.page_contents,
            'pages': _get_pages(self.paginator, self.page_number),
        })
        return ret

    def paginate_query(self, queryset):
        if self.exporting_csv_file:
            return queryset
        else:
            self.paginate(queryset)
            return self.page_contents

    def paginate(self, queryset):
        page = self.request.GET.get('page') or 1
        self.page_number = int(page)
        self.paginator = Paginator(queryset, ROWS_PER_PAGE)
        try:
            self.page_contents = self.paginator.page(page)
        except PageNotAnInteger:
            self.page_contents = self.paginator.page(1)
            page=1
        except EmptyPage:
            self.page_contents = self.paginator.page(self.paginator.num_pages)
            page = self.paginator.num_pages
        return page

    def get(self, *args, **kwargs):
        export = self.request.GET.get('export')
        if export == 'csv':
            return self.handle_csv_export()
        return super(BaseCMDBView, self).get(*args)

    def handle_csv_export(self):
        """
        Can overwite this for your needs
        """
        return self.do_csv_export()

    def do_csv_export(self):
        f = StringIO.StringIO()
        data = self.get_csv_data()
        csvutil.UnicodeWriter(f).writerows(data)
        response = HttpResponse(f.getvalue(), content_type="application/csv")
        response['Content-Disposition'] = 'attachment; filename=ralph.csv'
        return response


