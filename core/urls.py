from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register_patient, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_patient, name='dashboard_patient'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/reserver/', views.reserver_rdv, name='reserver_rdv'),
    path('dashboard/historique/', views.historique_rdv, name='historique_rdv'),
    path('dashboard/profil/', views.profil_patient, name='profil_patient'),
    path('dashboard/dossier/', views.dossier_medical_patient, name='dossier_medical_patient'),
    path('dashboard/paiement/', views.paiement_patient, name='paiement_patient'),
    path('medecin/dashboard/', views.dashboard_medecin, name='dashboard_medecin'),
    path('medecin/dossier/<int:patient_id>/', views.dossier_medical_medecin, name='dossier_medical_medecin'),
] 