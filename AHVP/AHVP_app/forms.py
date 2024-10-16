from django import forms
from .models import Muayene

class MuayeneForm(forms.ModelForm):
    class Meta:
        model = Muayene
        fields = [
            'hasta',  # Dropdown for selecting the patient
            'denge_bozuklugu', 'serebellar_bulgular', 'ense_sertligi', 'parkinsonizm',
            'kranial_sinir_bulgulari', 'motor_duygusal_bulgular', 'patolojik_refleks',
            'mmse', 'moca', 'acer',
            'tam_kan_hb', 'tam_kan_lym', 'tam_kan_neu', 'tam_kan_plt',
            'vitamin_b12', 'ast', 'alt', 'ldh', 'bun', 'kreatinin', 'uric_acid', 'eritrosit', 'sedim', 'vldrl',
            'bt_sonucu', 'mri_notlari', 'mri_tarihi', 'mri_freesurfer',
            'pet1', 'pet2', 'pet3', 'pet4', 'pet5', 'pet6', 'pet7', 'pet8', 'pet9', 'pet10',
            'pa_akciger_grafisi', 'ekg_sonucu', 'eeg_sonucu', 'ek_testler'
        ]
