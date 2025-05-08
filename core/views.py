from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Patient, Medecin, HoraireDisponible, RendezVous, DossierMedical, Observation, Ordonnance
from django.contrib import messages
from django import forms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone
from datetime import date, datetime, timedelta, time
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps

# Décorateur custom pour patient

def patient_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'patient_id' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Décorateur custom pour médecin

def medecin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'medecin_id' not in request.session:
            return redirect('login_medecin')
        return view_func(request, *args, **kwargs)
    return wrapper

# Create your views here.

class PatientRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    date_naissance = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'email', 'password', 'date_naissance']

def register_patient(request):
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.password = make_password(form.cleaned_data['password'])
            patient.save()
            messages.success(request, 'Inscription réussie. Connectez-vous.')
            return redirect('login')
    else:
        form = PatientRegisterForm()
    return render(request, 'core/register_patient.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        role = request.POST['role']
        email = request.POST['email']
        password = request.POST['password']
        if role == 'patient':
            try:
                patient = Patient.objects.get(email=email)
                if check_password(password, patient.password):
                    request.session['patient_id'] = patient.id
                    return redirect('dashboard_patient')
                else:
                    messages.error(request, 'Mot de passe incorrect')
            except Patient.DoesNotExist:
                messages.error(request, 'Email inconnu')
        elif role == 'medecin':
            try:
                medecin = Medecin.objects.get(email=email)
                if check_password(password, medecin.password):
                    request.session['medecin_id'] = medecin.id
                    return redirect('dashboard_medecin')
                else:
                    messages.error(request, 'Mot de passe incorrect')
            except Medecin.DoesNotExist:
                messages.error(request, 'Email inconnu')
    return render(request, 'core/login.html')

def landing(request):
    medecins = Medecin.objects.all()
    return render(request, 'core/landing.html', {'medecins': medecins})

@patient_login_required
def dashboard_patient(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    return render(request, 'core/dashboard_patient.html', {'patient': patient})

def logout_view(request):
    request.session.flush()
    return redirect('landing')

@patient_login_required
def reserver_rdv(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    medecins = Medecin.objects.all()
    horaires = None
    selected_medecin = request.GET.get('medecin')
    selected_date = request.GET.get('date')
    message = None
    if selected_medecin and selected_date:
        horaires = HoraireDisponible.objects.filter(
            medecin_id=selected_medecin,
            jour=selected_date
        )
        rdvs = RendezVous.objects.filter(medecin_id=selected_medecin, date__date=selected_date)
        heures_prises = [rdv.date.time() for rdv in rdvs]
        horaires = [h for h in horaires if h.heure_debut not in heures_prises]
    if request.method == 'POST':
        medecin_id = request.POST.get('medecin')
        date_str = request.POST.get('date')
        heure = request.POST.get('heure')
        if medecin_id and date_str and heure:
            dt = timezone.datetime.strptime(f"{date_str} {heure}", "%Y-%m-%d %H:%M")
            existe = RendezVous.objects.filter(medecin_id=medecin_id, date=dt).exists()
            if not existe:
                RendezVous.objects.create(
                    patient=patient,
                    medecin_id=medecin_id,
                    date=dt
                )
                message = "Rendez-vous réservé avec succès !"
            else:
                message = "Ce créneau n'est plus disponible."
    return render(request, 'core/reserver_rdv.html', {
        'medecins': medecins,
        'horaires': horaires,
        'selected_medecin': selected_medecin,
        'selected_date': selected_date,
        'message': message,
        'today': date.today().isoformat(),
    })

@patient_login_required
def historique_rdv(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    rdvs = RendezVous.objects.filter(patient=patient).select_related('medecin').order_by('-date')
    return render(request, 'core/historique_rdv.html', {'rdvs': rdvs})

class PatientEditForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'email', 'date_naissance']

@patient_login_required
def profil_patient(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    if request.method == 'POST':
        form = PatientEditForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profil_patient')
    else:
        form = PatientEditForm(instance=patient)
    return render(request, 'core/profil_patient.html', {'patient': patient, 'form': form})

@patient_login_required
def dossier_medical_patient(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    dossier = getattr(patient, 'dossiermedical', None)
    observations = dossier.observation_set.select_related('medecin').order_by('-date') if dossier else []
    ordonnances = dossier.ordonnance_set.select_related('medecin').order_by('-date') if dossier else []
    return render(request, 'core/dossier_medical_patient.html', {
        'observations': observations,
        'ordonnances': ordonnances
    })

@patient_login_required
def paiement_patient(request):
    patient_id = request.session['patient_id']
    patient = Patient.objects.get(id=patient_id)
    rdvs = RendezVous.objects.filter(patient=patient, facture_payee=False).select_related('medecin').order_by('-date')
    message = None
    if request.method == 'POST':
        rdv_id = request.POST.get('rdv_id')
        rdv = RendezVous.objects.filter(id=rdv_id, patient=patient).first()
        if rdv and not rdv.facture_payee:
            rdv.facture_payee = True
            rdv.save()
            message = "Paiement effectué avec succès !"
            rdvs = RendezVous.objects.filter(patient=patient, facture_payee=False).select_related('medecin').order_by('-date')
    return render(request, 'core/paiement_patient.html', {'rdvs': rdvs, 'message': message})

class MedecinLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

def login_medecin(request):
    if request.method == 'POST':
        form = MedecinLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                medecin = Medecin.objects.get(email=email)
                if check_password(password, medecin.password):
                    request.session['medecin_id'] = medecin.id
                    return redirect('dashboard_medecin')
                else:
                    messages.error(request, 'Mot de passe incorrect')
            except Medecin.DoesNotExist:
                messages.error(request, 'Email inconnu')
    else:
        form = MedecinLoginForm()
    return render(request, 'core/login_medecin.html', {'form': form})

@medecin_login_required
def dashboard_medecin(request):
    medecin_id = request.session['medecin_id']
    medecin = Medecin.objects.get(id=medecin_id)
    message = None

    # Semaine courante (lundi à samedi)
    today = datetime.today().date()
    lundi = today - timedelta(days=today.weekday())
    jours = [lundi + timedelta(days=i) for i in range(6)]  # Lundi à samedi
    horaires = [time(hour=h) for h in range(8, 16)]  # 8h à 15h inclus (créneaux d'1h)

    # Récupérer tous les RDV de la semaine
    rdvs = RendezVous.objects.filter(
        medecin=medecin,
        date__date__gte=jours[0],
        date__date__lte=jours[-1]
    ).select_related('patient')

    # Construire le planning
    planning = {jour: {h: None for h in horaires} for jour in jours}
    for rdv in rdvs:
        jour = rdv.date.date()
        heure = rdv.date.time().replace(minute=0, second=0, microsecond=0)
        if jour in planning and heure in planning[jour]:
            planning[jour][heure] = rdv

    return render(request, 'core/dashboard_medecin.html', {
        'planning': planning,
        'jours': jours,
        'horaires': horaires,
        'medecin': medecin,
        'message': message,
    })

@medecin_login_required
def dossier_medical_medecin(request, patient_id):
    medecin_id = request.session['medecin_id']
    medecin = Medecin.objects.get(id=medecin_id)
    patient = Patient.objects.get(id=patient_id)
    dossier, _ = DossierMedical.objects.get_or_create(patient=patient)
    observations = dossier.observation_set.select_related('medecin').order_by('-date')
    ordonnances = dossier.ordonnance_set.select_related('medecin').order_by('-date')
    message = None
    if request.method == 'POST':
        if 'observation' in request.POST:
            texte = request.POST.get('observation')
            if texte:
                Observation.objects.create(dossier=dossier, medecin=medecin, texte=texte)
                message = "Observation ajoutée."
        if 'ordonnance' in request.POST:
            texte = request.POST.get('ordonnance')
            if texte:
                Ordonnance.objects.create(dossier=dossier, medecin=medecin, texte=texte)
                message = "Ordonnance ajoutée."
        observations = dossier.observation_set.select_related('medecin').order_by('-date')
        ordonnances = dossier.ordonnance_set.select_related('medecin').order_by('-date')
    return render(request, 'core/dossier_medical_medecin.html', {
        'patient': patient,
        'observations': observations,
        'ordonnances': ordonnances,
        'message': message
    })

@medecin_login_required
def profil_medecin(request):
    medecin_id = request.session['medecin_id']
    medecin = Medecin.objects.get(id=medecin_id)
    return render(request, 'core/profil_medecin.html', {'medecin': medecin})
