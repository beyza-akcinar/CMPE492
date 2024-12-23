from django import forms
from .models import Muayene


class MuayeneForm(forms.ModelForm):
    class Meta:
        model = Muayene
        fields = [
            'hasta',  # Hasta seçimi için dropdown
            'sifrelenmis_tarih',  # Şifrelenmiş tarih bilgisi
            'visit_code',  # Ziyaret kodu
            'tani_encoding',  # Tanı kodu

            # Klinik test skorları
            'CDRSB', 
            'ADAS11', 
            'ADAS13', 
            'RAVLT_immediate', 
            'RAVLT_learning', 
            'RAVLT_forgetting',
            'FAQ',
        ]

class MuayeneAramaForm(forms.Form):
    isim = forms.CharField(required=False, label="Hasta İsmi")
    hasta_id = forms.CharField(required=False, label="Hasta ID")
    muayene_id = forms.CharField(required=False, label="Muayene ID")