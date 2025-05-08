from django.contrib import admin
from .models import Patient, Medecin, HoraireDisponible, DossierMedical, Observation, Ordonnance, RendezVous

@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('get_first_name', 'get_last_name', 'get_email', 'specialite', 'get_password')
    search_fields = ('first_name', 'last_name', 'email', 'specialite')

    def get_first_name(self, obj):
        return obj.first_name
    get_first_name.short_description = 'Prénom'

    def get_last_name(self, obj):
        return obj.last_name
    get_last_name.short_description = 'Nom'

    def get_email(self, obj):
        return obj.email
    get_email.short_description = 'Email'

    def get_password(self, obj):
        return obj.password
    get_password.short_description = 'Mot de passe (haché)'
    get_password.admin_order_field = 'password'



admin.site.register(Patient)
admin.site.register(HoraireDisponible)
admin.site.register(DossierMedical)
admin.site.register(Observation)
admin.site.register(Ordonnance)
admin.site.register(RendezVous)
