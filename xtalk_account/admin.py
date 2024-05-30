import swapper

from django.contrib import admin

from .models import OAuthState

admin.site.register(swapper.load_model('xtalk_account', 'User'))
admin.site.register(swapper.load_model('xtalk_account', 'RefreshToken'))
admin.site.register(swapper.load_model('xtalk_account', 'AccessToken'))


class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ('state', 'redirect_query')


admin.site.register(OAuthState, OAuthStateAdmin)
