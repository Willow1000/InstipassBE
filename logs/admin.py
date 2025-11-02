from django.contrib import admin
from .models import AdminActionsLog,BlackListLog,DemoLogs
# Register your models here.

class AdminActionsLogAdmin(admin.ModelAdmin):
    search_field = ("admin")
    list_display = ("admin",'victim_type')
    list_filter = ("admin","victim_type")

class BlackListLogAdmin(admin.ModelAdmin):
    search_field = ("admin")
    list_display = ("admin",'victim')
    list_filter = ("admin","victim")

class DemoLogsAdmin(admin.ModelAdmin):
    search_field = ("admin")
    list_display = ("admin",'demo')
    list_filter = ("admin","demo")


admin.site.register(AdminActionsLog,AdminActionsLogAdmin)
admin.site.register(BlackListLog,BlackListLogAdmin)
admin.site.register(DemoLogs,DemoLogsAdmin)
