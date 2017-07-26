from ralph.admin.filters import DateListFilter


class BuyoutDateFilter(DateListFilter):
    def queryset(self, request, queryset):
        queryset = super().queryset(request, queryset)
        if queryset is not None:
            queryset = queryset.filter(model__category__show_buyout_date=True)
        return queryset
