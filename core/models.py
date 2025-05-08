from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta, time

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # hashé
    date_naissance = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Medecin(models.Model):
    SPECIALITES = [
        ('cardiologie', 'Cardiologie'),
        ('dermatologie', 'Dermatologie'),
        ('pediatrie', 'Pédiatrie'),
        ('gynecologie', 'Gynécologie'),
        ('ophtalmologie', 'Ophtalmologie'),
        ('orthopedie', 'Orthopédie'),
        
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # hashé
    specialite = models.CharField(max_length=100, choices=SPECIALITES)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
        if is_new:
            from .models import HoraireDisponible
            for i in range(7):
                jour = (datetime.today() + timedelta(days=i)).date()
                if jour.weekday() < 6:  # Lundi=0, Samedi=5
                    for h in range(8, 16):
                        hd = time(hour=h, minute=0)
                        hf = time(hour=h+1, minute=0)
                        HoraireDisponible.objects.get_or_create(
                            medecin=self,
                            jour=jour,
                            heure_debut=hd,
                            heure_fin=hf
                        )

    def __str__(self):
        return f"Dr {self.first_name} {self.last_name} ({self.get_specialite_display()})"

class HoraireDisponible(models.Model):
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    jour = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

class DossierMedical(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)

class Observation(models.Model):
    dossier = models.ForeignKey(DossierMedical, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    texte = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

class Ordonnance(models.Model):
    dossier = models.ForeignKey(DossierMedical, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    texte = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

class RendezVous(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    date = models.DateTimeField()
    facture_payee = models.BooleanField(default=False)
