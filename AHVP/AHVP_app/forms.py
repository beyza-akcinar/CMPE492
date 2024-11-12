from django import forms
from .models import Muayene

class MuayeneForm(forms.ModelForm):
    class Meta:
        model = Muayene
        fields = [
            'hasta',  # Dropdown for selecting the patient
            'denge_bozuklugu', 'serebellar_bulgular', 'ense_sertligi', 'parkinsonizm',
            'kranial_sinir_bulgulari', 'motor_duygusal_bulgular', 'patolojik_refleks',
            'acer', 'npt', 'beck_depresyon', 'beck_anksiyete', 'geriatrik_depresyon', 'mmse', 'mmse_zaman', 'mmse_yer', 'mmse_kayithafizasi', 'mmse_dikkat', 'mmse_hatirlama', 'mmse_lisan',
            'glukoz', 'tam_kan_hb', 'tam_kan_lym', 'tam_kan_neu', 'tam_kan_plt',
            'vitamin_b12', 'tiroid_fonksiyon', 'ast', 'alt', 'ldh', 'bun', 'kreatinin', 'uric_acid', 'eritrosit', 'sedim', 'vldrl',
            'bt_sonucu', 'mri_notlari', 'mri_tarihi', 'mri_freesurfer',
            'pet1', 'pet2', 'pet3', 'pet4', 'pet5', 'pet6', 'pet7', 'pet8', 'pet9', 'pet10',
            'pa_akciger_grafisi', 'eeg_sonucu', 'eeg_file', 'amiloid','tau','ek_testler'
        ]

class MuayeneAramaForm(forms.Form):
    isim = forms.CharField(required=False, label="Hasta İsmi")
    hasta_id = forms.CharField(required=False, label="Hasta ID")
    muayene_id = forms.CharField(required=False, label="Muayene ID")