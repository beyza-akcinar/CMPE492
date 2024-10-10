from django.shortcuts import render, redirect
from .models import Hasta, Muayene

def home_view(request):
    return render(request, 'home.html')


def new_examination_view(request):
    if request.method == 'POST':
        # Get data from the form
        hasta_id = request.POST.get('hasta')
        visit_date = request.POST.get('visit_date')

        # Create a new Muayene instance and save to the database
        new_examination = Muayene(
            hasta_id=hasta_id,
            # The encrypted date will be set automatically in the save method
        )
        new_examination.save()

        return redirect('home') 

    # Fetch all Hasta records and combine names and surnames
    hasta_list = Hasta.objects.all()
    hasta_options = [(hasta.unique_hasta_id, f"{hasta.isim} {hasta.soyisim}") for hasta in hasta_list]

    return render(request, 'new_examination.html', {
        'hasta_options': hasta_options,
    })

def new_patient_view(request):
    if request.method == 'POST':
        # Get data from the form
        patient_name = request.POST.get('patient_name')
        patient_surname = request.POST.get('patient_surname')
        education_status = request.POST.get('education_status')
        city = request.POST.get('city')
        marital_status = request.POST.get('medeni')
        gender = request.POST.get('cinsiyet')
        age = request.POST.get('patient_age')
        print(f"Name: {patient_name}, Surname: {patient_surname}, Education: {education_status}, City: {city}, Marital Status: {marital_status}, Gender: {gender}")

        # Create a new Hasta instance and save to the database
        new_patient = Hasta(
            isim=patient_name,
            soyisim=patient_surname,
            egitim_durumu=education_status,
            sehir=city,
            medeni_durum=marital_status,
            cinsiyet=gender,
            yas=age,
        )
        new_patient.save()

        return redirect('home')

    return render(request, 'new_patient.html', {
        'city_options': Hasta.SEHIR_CHOICES,
        'cinsiyet_options': Hasta.CINSIYET_CHOICES,  # Pass gender choices
        'medeni_durum_options': Hasta.MEDENI_DURUM_CHOICES,
        'egitim_durum_options': Hasta.EGITIM_DURUM_CHOICES 
    })