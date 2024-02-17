from django.contrib import admin
from .models import ChatGptBot, ChatGptApiKey, ChatGptPdf, Profile

# Register your models here.


class ChatGptPdfAdmin(admin.ModelAdmin):
    list_display = ("speciality", "document",)
    list_filter = ["speciality", ]


class ProfileAdmin(admin.ModelAdmin):
    list_display = ("speciality", "user",)
    list_filter = ["speciality", ]


admin.site.register(ChatGptBot)
admin.site.register(ChatGptApiKey)
admin.site.register(ChatGptPdf, ChatGptPdfAdmin)
admin.site.register(Profile, ProfileAdmin)
