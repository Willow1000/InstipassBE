# # admin.py
# from django.contrib import admin
# from django.urls import path
# from django.shortcuts import redirect
# from InstiPass import view

# class ExportToolAdmin(admin.ModelAdmin):
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path('export-tool/', self.admin_site.admin_view(views.ExportToolView.as_view()), name='export_tool'),
#         ]
#         return custom_urls + urls

# # Register the export tool in admin
# admin.site.register_view('export-tool', view=views.ExportToolView.as_view(), name='export-tool')