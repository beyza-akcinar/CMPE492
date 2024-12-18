from django.shortcuts import render, redirect, get_object_or_404
from .models import Hasta, Muayene, FreeSurferSonuc, encrypt
from .forms import MuayeneForm
import pandas as pd
from django.db.models import Q, Count
import numpy as np
from django.http import HttpResponse
from django.db import models
from django.contrib import messages
import ast
from cryptography.fernet import Fernet
from datetime import datetime
from django.apps import apps
import csv
import os
import zipfile
from io import BytesIO
import math
import json
from .models import CINSIYET_CHOICES, MEDENI_DURUM_CHOICES, EGITIM_DURUM_CHOICES, SEHIR_CHOICES

def build_encoding_map(choices):
    return {choice[0]: idx for idx, choice in enumerate(choices)}

CINSIYET_ENCODING = build_encoding_map(CINSIYET_CHOICES)
MEDENI_DURUM_ENCODING = build_encoding_map(MEDENI_DURUM_CHOICES)
EGITIM_DURUM_ENCODING = build_encoding_map(EGITIM_DURUM_CHOICES)
SEHIR_ENCODING = build_encoding_map(SEHIR_CHOICES)

all_diagnoses = FreeSurferSonuc.objects.values_list('diagnosis', flat=True).distinct()
DIAGNOSIS_ENCODING = {diagnosis: idx for idx, diagnosis in enumerate(all_diagnoses)}

def patient_to_vector(hasta):
    # Base vector from Hasta
    base_vector = [
        CINSIYET_ENCODING.get(hasta.cinsiyet, -1),
        float(hasta.yas),
        SEHIR_ENCODING.get(hasta.sehir, -1),
        MEDENI_DURUM_ENCODING.get(hasta.medeni_durum, -1),
        EGITIM_DURUM_ENCODING.get(hasta.egitim_durumu, -1),
    ]

    # Get the Muayene with the largest ID
    muayene = Muayene.objects.filter(hasta=hasta).order_by('-id').first()

    if muayene:
        # Boolean fields as 1/0
        muayene_booleans = [
            int(muayene.denge_bozuklugu),
            int(muayene.serebellar_bulgular),
            int(muayene.ense_sertligi),
            int(muayene.parkinsonizm),
            int(muayene.kranial_sinir_bulgulari),
            int(muayene.motor_duygusal_bulgular),
            int(muayene.patolojik_refleks),
        ]

        # Cognitive tests (use 0 if None)
        muayene_cognitive = [
            muayene.acer or 0,
            muayene.npt or 0,
            muayene.beck_depresyon or 0,
            muayene.beck_anksiyete or 0,
            muayene.geriatrik_depresyon or 0,
            muayene.mmse_zaman or 0,
            muayene.mmse_yer or 0,
            muayene.mmse_kayithafizasi or 0,
            muayene.mmse_dikkat or 0,
            muayene.mmse_hatirlama or 0,
            muayene.mmse_lisan or 0,
            muayene.mmse or 0
        ]

        # Lab values
        muayene_lab = [
            float(muayene.glukoz or 0),
            float(muayene.tam_kan_hb or 0),
            float(muayene.tam_kan_lym or 0),
            float(muayene.tam_kan_neu or 0),
            float(muayene.tam_kan_plt or 0),
            float(muayene.vitamin_b12 or 0),
            float(muayene.tiroid_fonksiyon or 0),
            float(muayene.ast or 0),
            float(muayene.alt or 0),
            float(muayene.ldh or 0),
            float(muayene.bun or 0),
            float(muayene.kreatinin or 0),
            float(muayene.uric_acid or 0),
            float(muayene.eritrosit or 0),
            float(muayene.sedim or 0),
        ]

        # PET fields
        muayene_pet = [
            float(muayene.pet1 or 0),
            float(muayene.pet2 or 0),
            float(muayene.pet3 or 0),
            float(muayene.pet4 or 0),
            float(muayene.pet5 or 0),
            float(muayene.pet6 or 0),
            float(muayene.pet7 or 0),
            float(muayene.pet8 or 0),
            float(muayene.pet9 or 0),
            float(muayene.pet10 or 0)
        ]

        # FreeSurfer
        freesurfer = FreeSurferSonuc.objects.filter(muayene=muayene).first()
        freesurfer = FreeSurferSonuc.objects.filter(muayene=muayene).first()
        if freesurfer:
            # DecimalField değerlerini al
            freesurfer_fields = [f for f in FreeSurferSonuc._meta.get_fields() if isinstance(f, models.DecimalField)]

            # FreeSurfer DecimalField verilerini toplayın
            freesurfer_data = []
            for field in freesurfer_fields:
                value = getattr(freesurfer, field.name, None)
                freesurfer_data.append(float(value or 0))

            # Diagnosis alanını encode edip vektöre ekleyin
            encoded_diagnosis = DIAGNOSIS_ENCODING.get(freesurfer.diagnosis, -1)  # Eğer diagnosis bulunamazsa -1 kullan
            freesurfer_data.append(encoded_diagnosis)
        else:
            # No FreeSurfer data
            
            freesurfer_fields = [f for f in FreeSurferSonuc._meta.get_fields() if isinstance(f, models.DecimalField)]
            freesurfer_data = [0]*len(freesurfer_fields)
    else:
        # No Muayene found:
        muayene_booleans = [0]*7
        muayene_cognitive = [0]*12
        muayene_lab = [0]*15
        muayene_pet = [0]*10
        freesurfer_fields = [f for f in FreeSurferSonuc._meta.get_fields() if isinstance(f, models.DecimalField)]
        freesurfer_data = [0]*len(freesurfer_fields)

    full_vector = base_vector + muayene_booleans + muayene_cognitive + muayene_lab + muayene_pet + freesurfer_data
    return full_vector

def normalize_vector(vector):
    min_val = min(vector)
    max_val = max(vector)
    if max_val == min_val:  # Eğer tüm değerler aynıysa hepsini 0 yap
        return [0.0] * len(vector)
    return [(x - min_val) / (max_val - min_val) for x in vector]
    
def scale_vectors(vectors):
    # vectors: list of lists
    # Transpose to get columns
    cols = list(zip(*vectors))
    scaled_cols = []
    for col in cols:
        col_min = min(col)
        col_max = max(col)
        scaled_col = normalize_vector(col)
        scaled_cols.append(scaled_col)
    # Transpose back
    scaled_vectors = list(zip(*scaled_cols))
    return [list(vec) for vec in scaled_vectors]

def cosine_similarity(vec1, vec2):
    # Calculate cosine similarity between two vectors
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 > 0 and norm2 > 0:  # Avoid division by zero
        return dot_product / (norm1 * norm2)
    else:
        return 0.0

def home_view(request):
    return render(request, 'home.html')

def new_examination_view(request):
    if request.method == 'POST':
        form = MuayeneForm(request.POST, request.FILES)
        if form.is_valid():
            muayene_instance = form.save()
            # FreeSurfer dosyasını al
            mri_freesurfer_file = request.FILES.get('mri_freesurfer')
            if mri_freesurfer_file:
                # FreeSurfer dosyasını işle ve veritabanına kaydet
                process_freesurfer_file(mri_freesurfer_file, muayene_instance)

            return redirect('home')  # Başarılı kayıt sonrası yönlendirme
   
    else:
        form = MuayeneForm()
    
    hasta_list = Hasta.objects.all()
    hasta_options = [(hasta.hasta_id, f"{hasta.isim} {hasta.soyisim}") for hasta in hasta_list]

    return render(request, 'new_examination.html', {
        'hasta_options': hasta_options,
        'form': form
    })

mri_fields = ['id', 'muayene', 'diagnosis', 'lh_cortex_vol', 'rh_cortex_vol', 'brain_seg_vol_not_vent', 'ventricle_choroid_vol', 'cortex_vol', 'brain_seg_vol', 'lh_cerebral_white_matter_vol', 'rh_cerebral_white_matter_vol', 'cerebral_white_matter_vol', 'subcort_gray_vol', 'total_gray_vol', 'supra_tentorial_vol', 'supra_tentorial_vol_not_vent', 'mask_vol', 'brain_seg_vol_to_etiv', 'mask_vol_to_etiv', 'lh_surface_holes', 'rh_surface_holes', 'surface_holes', 'etiv', 'left_lateral_ventricle_volume_mm3', 'left_lateral_ventricle_normmean', 'left_lateral_ventricle_normstddev', 'left_lateral_ventricle_normmin', 'left_lateral_ventricle_normmax', 'left_lateral_ventricle_normrange', 'left_inf_lat_vent_volume_mm3', 'left_inf_lat_vent_normmean', 'left_inf_lat_vent_normstddev', 'left_inf_lat_vent_normmin', 'left_inf_lat_vent_normmax', 'left_inf_lat_vent_normrange', 'left_cerebellum_white_matter_volume_mm3', 'left_cerebellum_white_matter_normmean', 'left_cerebellum_white_matter_normstddev', 'left_cerebellum_white_matter_normmin', 'left_cerebellum_white_matter_normmax', 'left_cerebellum_white_matter_normrange', 'left_cerebellum_cortex_volume_mm3', 'left_cerebellum_cortex_normmean', 'left_cerebellum_cortex_normstddev', 'left_cerebellum_cortex_normmin', 'left_cerebellum_cortex_normmax', 'left_cerebellum_cortex_normrange', 'left_thalamus_volume_mm3', 'left_thalamus_normmean', 'left_thalamus_normstddev', 'left_thalamus_normmin', 'left_thalamus_normmax', 'left_thalamus_normrange', 'left_caudate_volume_mm3', 'left_caudate_normmean', 'left_caudate_normstddev', 'left_caudate_normmin', 'left_caudate_normmax', 'left_caudate_normrange', 'left_putamen_volume_mm3', 'left_putamen_normmean', 'left_putamen_normstddev', 'left_putamen_normmin', 'left_putamen_normmax', 'left_putamen_normrange', 'left_pallidum_volume_mm3', 'left_pallidum_normmean', 'left_pallidum_normstddev', 'left_pallidum_normmin', 'left_pallidum_normmax', 'left_pallidum_normrange', 'the3rd_ventricle_volume_mm3', 'the3rd_ventricle_normmean', 'the3rd_ventricle_normstddev', 'the3rd_ventricle_normmin', 'the3rd_ventricle_normmax', 'the3rd_ventricle_normrange', 'the4th_ventricle_volume_mm3', 'the4th_ventricle_normmean', 'the4th_ventricle_normstddev', 'the4th_ventricle_normmin', 'the4th_ventricle_normmax', 'the4th_ventricle_normrange', 'brain_stem_volume_mm3', 'brain_stem_normmean', 'brain_stem_normstddev', 'brain_stem_normmin', 'brain_stem_normmax', 'brain_stem_normrange', 'left_hippocampus_volume_mm3', 'left_hippocampus_normmean', 'left_hippocampus_normstddev', 'left_hippocampus_normmin', 'left_hippocampus_normmax', 'left_hippocampus_normrange', 'left_amygdala_volume_mm3', 'left_amygdala_normmean', 'left_amygdala_normstddev', 'left_amygdala_normmin', 'left_amygdala_normmax', 'left_amygdala_normrange', 'csf_volume_mm3', 'csf_normmean', 'csf_normstddev', 'csf_normmin', 'csf_normmax', 'csf_normrange', 'left_accumbens_area_volume_mm3', 'left_accumbens_area_normmean', 'left_accumbens_area_normstddev', 'left_accumbens_area_normmin', 'left_accumbens_area_normmax', 'left_accumbens_area_normrange', 'left_ventraldc_volume_mm3', 'left_ventraldc_normmean', 'left_ventraldc_normstddev', 'left_ventraldc_normmin', 'left_ventraldc_normmax', 'left_ventraldc_normrange', 'left_vessel_volume_mm3', 'left_vessel_normmean', 'left_vessel_normstddev', 'left_vessel_normmin', 'left_vessel_normmax', 'left_vessel_normrange', 'left_choroid_plexus_volume_mm3', 'left_choroid_plexus_normmean', 'left_choroid_plexus_normstddev', 'left_choroid_plexus_normmin', 'left_choroid_plexus_normmax', 'left_choroid_plexus_normrange', 'right_lateral_ventricle_volume_mm3', 'right_lateral_ventricle_normmean', 'right_lateral_ventricle_normstddev', 'right_lateral_ventricle_normmin', 'right_lateral_ventricle_normmax', 'right_lateral_ventricle_normrange', 'right_inf_lat_vent_volume_mm3', 'right_inf_lat_vent_normmean', 'right_inf_lat_vent_normstddev', 'right_inf_lat_vent_normmin', 'right_inf_lat_vent_normmax', 'right_inf_lat_vent_normrange', 'right_cerebellum_white_matter_volume_mm3', 'right_cerebellum_white_matter_normmean', 'right_cerebellum_white_matter_normstddev', 'right_cerebellum_white_matter_normmin', 'right_cerebellum_white_matter_normmax', 'right_cerebellum_white_matter_normrange', 'right_cerebellum_cortex_volume_mm3', 'right_cerebellum_cortex_normmean', 'right_cerebellum_cortex_normstddev', 'right_cerebellum_cortex_normmin', 'right_cerebellum_cortex_normmax', 'right_cerebellum_cortex_normrange', 'right_thalamus_volume_mm3', 'right_thalamus_normmean', 'right_thalamus_normstddev', 'right_thalamus_normmin', 'right_thalamus_normmax', 'right_thalamus_normrange', 'right_caudate_volume_mm3', 'right_caudate_normmean', 'right_caudate_normstddev', 'right_caudate_normmin', 'right_caudate_normmax', 'right_caudate_normrange', 'right_putamen_volume_mm3', 'right_putamen_normmean', 'right_putamen_normstddev', 'right_putamen_normmin', 'right_putamen_normmax', 'right_putamen_normrange', 'right_pallidum_volume_mm3', 'right_pallidum_normmean', 'right_pallidum_normstddev', 'right_pallidum_normmin', 'right_pallidum_normmax', 'right_pallidum_normrange', 'right_hippocampus_volume_mm3', 'right_hippocampus_normmean', 'right_hippocampus_normstddev', 'right_hippocampus_normmin', 'right_hippocampus_normmax', 'right_hippocampus_normrange', 'right_amygdala_volume_mm3', 'right_amygdala_normmean', 'right_amygdala_normstddev', 'right_amygdala_normmin', 'right_amygdala_normmax', 'right_amygdala_normrange', 'right_accumbens_area_volume_mm3', 'right_accumbens_area_normmean', 'right_accumbens_area_normstddev', 'right_accumbens_area_normmin', 'right_accumbens_area_normmax', 'right_accumbens_area_normrange', 'right_ventraldc_volume_mm3', 'right_ventraldc_normmean', 'right_ventraldc_normstddev', 'right_ventraldc_normmin', 'right_ventraldc_normmax', 'right_ventraldc_normrange', 'right_vessel_volume_mm3', 'right_vessel_normmean', 'right_vessel_normstddev', 'right_vessel_normmin', 'right_vessel_normmax', 'right_vessel_normrange', 'right_choroid_plexus_volume_mm3', 'right_choroid_plexus_normmean', 'right_choroid_plexus_normstddev', 'right_choroid_plexus_normmin', 'right_choroid_plexus_normmax', 'right_choroid_plexus_normrange', 'the5th_ventricle_volume_mm3', 'the5th_ventricle_normmean', 'the5th_ventricle_normstddev', 'the5th_ventricle_normmin', 'the5th_ventricle_normmax', 'the5th_ventricle_normrange', 'wm_hypointensities_volume_mm3', 'wm_hypointensities_normmean', 'wm_hypointensities_normstddev', 'wm_hypointensities_normmin', 'wm_hypointensities_normmax', 'wm_hypointensities_normrange', 'left_wm_hypointensities_volume_mm3', 'left_wm_hypointensities_normmean', 'left_wm_hypointensities_normstddev', 'left_wm_hypointensities_normmin', 'left_wm_hypointensities_normmax', 'left_wm_hypointensities_normrange', 'right_wm_hypointensities_volume_mm3', 'right_wm_hypointensities_normmean', 'right_wm_hypointensities_normstddev', 'right_wm_hypointensities_normmin', 'right_wm_hypointensities_normmax', 'right_wm_hypointensities_normrange', 'non_wm_hypointensities_volume_mm3', 'non_wm_hypointensities_normmean', 'non_wm_hypointensities_normstddev', 'non_wm_hypointensities_normmin', 'non_wm_hypointensities_normmax', 'non_wm_hypointensities_normrange', 'left_non_wm_hypointensities_volume_mm3', 'left_non_wm_hypointensities_normmean', 'left_non_wm_hypointensities_normstddev', 'left_non_wm_hypointensities_normmin', 'left_non_wm_hypointensities_normmax', 'left_non_wm_hypointensities_normrange', 'right_non_wm_hypointensities_volume_mm3', 'right_non_wm_hypointensities_normmean', 'right_non_wm_hypointensities_normstddev', 'right_non_wm_hypointensities_normmin', 'right_non_wm_hypointensities_normmax', 'right_non_wm_hypointensities_normrange', 'optic_chiasm_volume_mm3', 'optic_chiasm_normmean', 'optic_chiasm_normstddev', 'optic_chiasm_normmin', 'optic_chiasm_normmax', 'optic_chiasm_normrange', 'cc_posterior_volume_mm3', 'cc_posterior_normmean', 'cc_posterior_normstddev', 'cc_posterior_normmin', 'cc_posterior_normmax', 'cc_posterior_normrange', 'cc_mid_posterior_volume_mm3', 'cc_mid_posterior_normmean', 'cc_mid_posterior_normstddev', 'cc_mid_posterior_normmin', 'cc_mid_posterior_normmax', 'cc_mid_posterior_normrange', 'cc_central_volume_mm3', 'cc_central_normmean', 'cc_central_normstddev', 'cc_central_normmin', 'cc_central_normmax', 'cc_central_normrange', 'cc_mid_anterior_volume_mm3', 'cc_mid_anterior_normmean', 'cc_mid_anterior_normstddev', 'cc_mid_anterior_normmin', 'cc_mid_anterior_normmax', 'cc_mid_anterior_normrange', 'cc_anterior_volume_mm3', 'cc_anterior_normmean', 'cc_anterior_normstddev', 'cc_anterior_normmin', 'cc_anterior_normmax', 'cc_anterior_normrange']

def get_pretty_attribute_name(attribute_name):
    attribute_mapping = {
        'id': 'Muayene ID',
        'muayene': 'Hasta ID',
        'diagnosis': 'Tanı',
        'lh_cortex_vol': 'LH Cortex Volume',
        'rh_cortex_vol': 'RH Cortex Volume',
        'brain_seg_vol_not_vent': 'Brain Seg Vol Not Vent',
        'ventricle_choroid_vol': 'Ventricle Choroid Volume',
        'cortex_vol': 'Cortex Volume',
        'brain_seg_vol': 'Brain Segmentation Volume',
        'lh_cerebral_white_matter_vol': 'Left Hemisphere Cerebral White Matter Volume',
        'rh_cerebral_white_matter_vol': 'Right Hemisphere Cerebral White Matter Volume',
        'cerebral_white_matter_vol': 'Cerebral White Matter Volume',
        'subcort_gray_vol': 'Subcortical Gray Matter Volume',
        'total_gray_vol': 'Total Gray Matter Volume',
        'supra_tentorial_vol': 'Supra Tentorial Volume',
        'supra_tentorial_vol_not_vent': 'Supra Tentorial Volume (No Ventricle)',
        'mask_vol': 'Mask Volume',
        'brain_seg_vol_to_etiv': 'Brain Segmentation Volume to eTIV',
        'mask_vol_to_etiv': 'Mask Volume to eTIV',
        'lh_surface_holes': 'Left Hemisphere Surface Holes',
        'rh_surface_holes': 'Right Hemisphere Surface Holes',
        'surface_holes': 'Surface Holes',
        'etiv': 'Estimated Total Intracranial Volume (eTIV)',
        'left_lateral_ventricle_volume_mm3': 'Left Lateral Ventricle Volume (mm3)',
        'left_lateral_ventricle_normmean': 'Left Lateral Ventricle Norm Mean',
        'left_lateral_ventricle_normstddev': 'Left Lateral Ventricle Norm Std Dev',
        'left_lateral_ventricle_normmin': 'Left Lateral Ventricle Norm Min',
        'left_lateral_ventricle_normmax': 'Left Lateral Ventricle Norm Max',
        'left_lateral_ventricle_normrange': 'Left Lateral Ventricle Norm Range',
        'left_inf_lat_vent_volume_mm3': 'Left Inferior Lateral Ventricle Volume (mm3)',
        'left_inf_lat_vent_normmean': 'Left Inferior Lateral Ventricle Norm Mean',
        'left_inf_lat_vent_normstddev': 'Left Inferior Lateral Ventricle Norm Std Dev',
        'left_inf_lat_vent_normmin': 'Left Inferior Lateral Ventricle Norm Min',
        'left_inf_lat_vent_normmax': 'Left Inferior Lateral Ventricle Norm Max',
        'left_inf_lat_vent_normrange': 'Left Inferior Lateral Ventricle Norm Range',
        'left_cerebellum_white_matter_volume_mm3': 'Left Cerebellum White Matter Volume (mm3)',
        'left_cerebellum_white_matter_normmean': 'Left Cerebellum White Matter Norm Mean',
        'left_cerebellum_white_matter_normstddev': 'Left Cerebellum White Matter Norm Std Dev',
        'left_cerebellum_white_matter_normmin': 'Left Cerebellum White Matter Norm Min',
        'left_cerebellum_white_matter_normmax': 'Left Cerebellum White Matter Norm Max',
        'left_cerebellum_white_matter_normrange': 'Left Cerebellum White Matter Norm Range',
        'left_cerebellum_cortex_volume_mm3': 'Left Cerebellum Cortex Volume (mm3)',
        'left_cerebellum_cortex_normmean': 'Left Cerebellum Cortex Norm Mean',
        'left_cerebellum_cortex_normstddev': 'Left Cerebellum Cortex Norm Std Dev',
        'left_cerebellum_cortex_normmin': 'Left Cerebellum Cortex Norm Min',
        'left_cerebellum_cortex_normmax': 'Left Cerebellum Cortex Norm Max',
        'left_cerebellum_cortex_normrange': 'Left Cerebellum Cortex Norm Range',
        'left_thalamus_volume_mm3': 'Left Thalamus Volume (mm3)',
        'left_thalamus_normmean': 'Left Thalamus Norm Mean',
        'left_thalamus_normstddev': 'Left Thalamus Norm Std Dev',
        'left_thalamus_normmin': 'Left Thalamus Norm Min',
        'left_thalamus_normmax': 'Left Thalamus Norm Max',
        'left_thalamus_normrange': 'Left Thalamus Norm Range',
        'left_caudate_volume_mm3': 'Left Caudate Volume (mm3)',
        'left_caudate_normmean': 'Left Caudate Norm Mean',
        'left_caudate_normstddev': 'Left Caudate Norm Std Dev',
        'left_caudate_normmin': 'Left Caudate Norm Min',
        'left_caudate_normmax': 'Left Caudate Norm Max',
        'left_caudate_normrange': 'Left Caudate Norm Range',
        'left_putamen_volume_mm3': 'Left Putamen Volume (mm3)',
        'left_putamen_normmean': 'Left Putamen Norm Mean',
        'left_putamen_normstddev': 'Left Putamen Norm Std Dev',
        'left_putamen_normmin': 'Left Putamen Norm Min',
        'left_putamen_normmax': 'Left Putamen Norm Max',
        'left_putamen_normrange': 'Left Putamen Norm Range',
        'left_pallidum_volume_mm3': 'Left Pallidum Volume (mm3)',
        'left_pallidum_normmean': 'Left Pallidum Norm Mean',
        'left_pallidum_normstddev': 'Left Pallidum Norm Std Dev',
        'left_pallidum_normmin': 'Left Pallidum Norm Min',
        'left_pallidum_normmax': 'Left Pallidum Norm Max',
        'left_pallidum_normrange': 'Left Pallidum Norm Range',
        'the3rd_ventricle_volume_mm3': '3rd Ventricle Volume (mm3)',
        'the3rd_ventricle_normmean': '3rd Ventricle Norm Mean',
        'the3rd_ventricle_normstddev': '3rd Ventricle Norm Std Dev',
        'the3rd_ventricle_normmin': '3rd Ventricle Norm Min',
        'the3rd_ventricle_normmax': '3rd Ventricle Norm Max',
        'the3rd_ventricle_normrange': '3rd Ventricle Norm Range',
        'the4th_ventricle_volume_mm3': '4th Ventricle Volume (mm3)',
        'the4th_ventricle_normmean': '4th Ventricle Norm Mean',
        'the4th_ventricle_normstddev': '4th Ventricle Norm Std Dev',
        'the4th_ventricle_normmin': '4th Ventricle Norm Min',
        'the4th_ventricle_normmax': '4th Ventricle Norm Max',
        'the4th_ventricle_normrange': '4th Ventricle Norm Range',
        'brain_stem_volume_mm3': 'Brain Stem Volume (mm3)',
        'brain_stem_normmean': 'Brain Stem Norm Mean',
        'brain_stem_normstddev': 'Brain Stem Norm Std Dev',
        'brain_stem_normmin': 'Brain Stem Norm Min',
        'brain_stem_normmax': 'Brain Stem Norm Max',
        'brain_stem_normrange': 'Brain Stem Norm Range',
        'left_hippocampus_volume_mm3': 'Left Hippocampus Volume (mm3)',
        'left_hippocampus_normmean': 'Left Hippocampus Norm Mean',
        'left_hippocampus_normstddev': 'Left Hippocampus Norm Std Dev',
        'left_hippocampus_normmin': 'Left Hippocampus Norm Min',
        'left_hippocampus_normmax': 'Left Hippocampus Norm Max',
        'left_hippocampus_normrange': 'Left Hippocampus Norm Range',
        'left_amygdala_volume_mm3': 'Left Amygdala Volume (mm3)',
        'left_amygdala_normmean': 'Left Amygdala Norm Mean',
        'left_amygdala_normstddev': 'Left Amygdala Norm Std Dev',
        'left_amygdala_normmin': 'Left Amygdala Norm Min',
        'left_amygdala_normmax': 'Left Amygdala Norm Max',
        'left_amygdala_normrange': 'Left Amygdala Norm Range',
        'csf_volume_mm3': 'CSF Volume (mm3)',
        'csf_normmean': 'CSF Norm Mean',
        'csf_normstddev': 'CSF Norm Std Dev',
        'csf_normmin': 'CSF Norm Min',
        'csf_normmax': 'CSF Norm Max',
        'csf_normrange': 'CSF Norm Range',
        'left_accumbens_area_volume_mm3': 'Left Accumbens Area Volume (mm3)',
        'left_accumbens_area_normmean': 'Left Accumbens Area Norm Mean',
        'left_accumbens_area_normstddev': 'Left Accumbens Area Norm Std Dev',
        'left_accumbens_area_normmin': 'Left Accumbens Area Norm Min',
        'left_accumbens_area_normmax': 'Left Accumbens Area Norm Max',
        'left_accumbens_area_normrange': 'Left Accumbens Area Norm Range',
        'left_ventraldc_volume_mm3': 'Left Ventral DC Volume (mm3)',
        'left_ventraldc_normmean': 'Left Ventral DC Norm Mean',
        'left_ventraldc_normstddev': 'Left Ventral DC Norm Std Dev',
        'left_ventraldc_normmin': 'Left Ventral DC Norm Min',
        'left_ventraldc_normmax': 'Left Ventral DC Norm Max',
        'left_ventraldc_normrange': 'Left Ventral DC Norm Range',
        'left_vessel_volume_mm3': 'Left Vessel Volume (mm3)',
        'left_vessel_normmean': 'Left Vessel Norm Mean',
        'left_vessel_normstddev': 'Left Vessel Norm Std Dev',
        'left_vessel_normmin': 'Left Vessel Norm Min',
        'left_vessel_normmax': 'Left Vessel Norm Max',
        'left_vessel_normrange': 'Left Vessel Norm Range',
        'left_choroid_plexus_volume_mm3': 'Left Choroid Plexus Volume (mm3)',
        'left_choroid_plexus_normmean': 'Left Choroid Plexus Norm Mean',
        'left_choroid_plexus_normstddev': 'Left Choroid Plexus Norm Std Dev',
        'left_choroid_plexus_normmin': 'Left Choroid Plexus Norm Min',
        'left_choroid_plexus_normmax': 'Left Choroid Plexus Norm Max',
        'left_choroid_plexus_normrange': 'Left Choroid Plexus Norm Range',
        'right_lateral_ventricle_volume_mm3': 'Right Lateral Ventricle Volume (mm3)',
        'right_lateral_ventricle_normmean': 'Right Lateral Ventricle Norm Mean',
        'right_lateral_ventricle_normstddev': 'Right Lateral Ventricle Norm Std Dev',
        'right_lateral_ventricle_normmin': 'Right Lateral Ventricle Norm Min',
        'right_lateral_ventricle_normmax': 'Right Lateral Ventricle Norm Max',
        'right_lateral_ventricle_normrange': 'Right Lateral Ventricle Norm Range',
        'right_inf_lat_vent_volume_mm3': 'Right Inferior Lateral Ventricle Volume (mm3)',
        'right_inf_lat_vent_normmean': 'Right Inferior Lateral Ventricle Norm Mean',
        'right_inf_lat_vent_normstddev': 'Right Inferior Lateral Ventricle Norm Std Dev',
        'right_inf_lat_vent_normmin': 'Right Inferior Lateral Ventricle Norm Min',
        'right_inf_lat_vent_normmax': 'Right Inferior Lateral Ventricle Norm Max',
        'right_inf_lat_vent_normrange': 'Right Inferior Lateral Ventricle Norm Range',
        'right_cerebellum_white_matter_volume_mm3': 'Right Cerebellum White Matter Volume (mm3)',
        'right_cerebellum_white_matter_normmean': 'Right Cerebellum White Matter Norm Mean',
        'right_cerebellum_white_matter_normstddev': 'Right Cerebellum White Matter Norm Std Dev',
        'right_cerebellum_white_matter_normmin': 'Right Cerebellum White Matter Norm Min',
        'right_cerebellum_white_matter_normmax': 'Right Cerebellum White Matter Norm Max',
        'right_cerebellum_white_matter_normrange': 'Right Cerebellum White Matter Norm Range',
        'right_cerebellum_cortex_volume_mm3': 'Right Cerebellum Cortex Volume (mm3)',
        'right_cerebellum_cortex_normmean': 'Right Cerebellum Cortex Norm Mean',
        'right_cerebellum_cortex_normstddev': 'Right Cerebellum Cortex Norm Std Dev',
        'right_cerebellum_cortex_normmin': 'Right Cerebellum Cortex Norm Min',
        'right_cerebellum_cortex_normmax': 'Right Cerebellum Cortex Norm Max',
        'right_cerebellum_cortex_normrange': 'Right Cerebellum Cortex Norm Range',
        'right_thalamus_volume_mm3': 'Right Thalamus Volume (mm3)',
        'right_thalamus_normmean': 'Right Thalamus Norm Mean',
        'right_thalamus_normstddev': 'Right Thalamus Norm Std Dev',
        'right_thalamus_normmin': 'Right Thalamus Norm Min',
        'right_thalamus_normmax': 'Right Thalamus Norm Max',
        'right_thalamus_normrange': 'Right Thalamus Norm Range',
        'right_caudate_volume_mm3': 'Right Caudate Volume (mm3)',
        'right_caudate_normmean': 'Right Caudate Norm Mean',
        'right_caudate_normstddev': 'Right Caudate Norm Std Dev',
        'right_caudate_normmin': 'Right Caudate Norm Min',
        'right_caudate_normmax': 'Right Caudate Norm Max',
        'right_caudate_normrange': 'Right Caudate Norm Range',
        'right_putamen_volume_mm3': 'Right Putamen Volume (mm3)',
        'right_putamen_normmean': 'Right Putamen Norm Mean',
        'right_putamen_normstddev': 'Right Putamen Norm Std Dev',
        'right_putamen_normmin': 'Right Putamen Norm Min',
        'right_putamen_normmax': 'Right Putamen Norm Max',
        'right_putamen_normrange': 'Right Putamen Norm Range',
        'right_pallidum_volume_mm3': 'Right Pallidum Volume (mm3)',
        'right_pallidum_normmean': 'Right Pallidum Norm Mean',
        'right_pallidum_normstddev': 'Right Pallidum Norm Std Dev',
        'right_pallidum_normmin': 'Right Pallidum Norm Min',
        'right_pallidum_normmax': 'Right Pallidum Norm Max',
        'right_pallidum_normrange': 'Right Pallidum Norm Range',
        'right_hippocampus_volume_mm3': 'Right Hippocampus Volume (mm3)',
        'right_hippocampus_normmean': 'Right Hippocampus Norm Mean',
        'right_hippocampus_normstddev': 'Right Hippocampus Norm Std Dev',
        'right_hippocampus_normmin': 'Right Hippocampus Norm Min',
        'right_hippocampus_normmax': 'Right Hippocampus Norm Max',
        'right_hippocampus_normrange': 'Right Hippocampus Norm Range',
        'right_amygdala_volume_mm3': 'Right Amygdala Volume (mm3)',
        'right_amygdala_normmean': 'Right Amygdala Norm Mean',
        'right_amygdala_normstddev': 'Right Amygdala Norm Std Dev',
        'right_amygdala_normmin': 'Right Amygdala Norm Min',
        'right_amygdala_normmax': 'Right Amygdala Norm Max',
        'right_amygdala_normrange': 'Right Amygdala Norm Range',
        'right_accumbens_area_volume_mm3': 'Right Accumbens Area Volume (mm3)',
        'right_accumbens_area_normmean': 'Right Accumbens Area Norm Mean',
        'right_accumbens_area_normstddev': 'Right Accumbens Area Norm Std Dev',
        'right_accumbens_area_normmin': 'Right Accumbens Area Norm Min',
        'right_accumbens_area_normmax': 'Right Accumbens Area Norm Max',
        'right_accumbens_area_normrange': 'Right Accumbens Area Norm Range',
        'right_ventraldc_volume_mm3': 'Right Ventral DC Volume (mm3)',
        'right_ventraldc_normmean': 'Right Ventral DC Norm Mean',
        'right_ventraldc_normstddev': 'Right Ventral DC Norm Std Dev',
        'right_ventraldc_normmin': 'Right Ventral DC Norm Min',
        'right_ventraldc_normmax': 'Right Ventral DC Norm Max',
        'right_ventraldc_normrange': 'Right Ventral DC Norm Range',
        'right_vessel_volume_mm3': 'Right Vessel Volume (mm3)',
        'right_vessel_normmean': 'Right Vessel Norm Mean',
        'right_vessel_normstddev': 'Right Vessel Norm Std Dev',
        'right_vessel_normmin': 'Right Vessel Norm Min',
        'right_vessel_normmax': 'Right Vessel Norm Max',
        'right_vessel_normrange': 'Right Vessel Norm Range',
        'right_choroid_plexus_volume_mm3': 'Right Choroid Plexus Volume (mm3)',
        'right_choroid_plexus_normmean': 'Right Choroid Plexus Norm Mean',
        'right_choroid_plexus_normstddev': 'Right Choroid Plexus Norm Std Dev',
        'right_choroid_plexus_normmin': 'Right Choroid Plexus Norm Min',
        'right_choroid_plexus_normmax': 'Right Choroid Plexus Norm Max',
        'right_choroid_plexus_normrange': 'Right Choroid Plexus Norm Range',
        'the5th_ventricle_volume_mm3': '5th Ventricle Volume (mm3)',
        'the5th_ventricle_normmean': '5th Ventricle Norm Mean',
        'the5th_ventricle_normstddev': '5th Ventricle Norm Std Dev',
        'the5th_ventricle_normmin': '5th Ventricle Norm Min',
        'the5th_ventricle_normmax': '5th Ventricle Norm Max',
        'the5th_ventricle_normrange': '5th Ventricle Norm Range',
        'wm_hypointensities_volume_mm3': 'WM Hypointensities Volume (mm3)',
        'wm_hypointensities_normmean': 'WM Hypointensities Norm Mean',
        'wm_hypointensities_normstddev': 'WM Hypointensities Norm Std Dev',
        'wm_hypointensities_normmin': 'WM Hypointensities Norm Min',
        'wm_hypointensities_normmax': 'WM Hypointensities Norm Max',
        'wm_hypointensities_normrange': 'WM Hypointensities Norm Range',
        'left_wm_hypointensities_volume_mm3': 'Left WM Hypointensities Volume (mm3)',
        'left_wm_hypointensities_normmean': 'Left WM Hypointensities Norm Mean',
        'left_wm_hypointensities_normstddev': 'Left WM Hypointensities Norm Std Dev',
        'left_wm_hypointensities_normmin': 'Left WM Hypointensities Norm Min',
        'left_wm_hypointensities_normmax': 'Left WM Hypointensities Norm Max',
        'left_wm_hypointensities_normrange': 'Left WM Hypointensities Norm Range',
        'right_wm_hypointensities_volume_mm3': 'Right WM Hypointensities Volume (mm3)',
        'right_wm_hypointensities_normmean': 'Right WM Hypointensities Norm Mean',
        'right_wm_hypointensities_normstddev': 'Right WM Hypointensities Norm Std Dev',
        'right_wm_hypointensities_normmin': 'Right WM Hypointensities Norm Min',
        'right_wm_hypointensities_normmax': 'Right WM Hypointensities Norm Max',
        'right_wm_hypointensities_normrange': 'Right WM Hypointensities Norm Range',
        'non_wm_hypointensities_volume_mm3': 'Non-WM Hypointensities Volume (mm3)',
        'non_wm_hypointensities_normmean': 'Non-WM Hypointensities Norm Mean',
        'non_wm_hypointensities_normstddev': 'Non-WM Hypointensities Norm Std Dev',
        'non_wm_hypointensities_normmin': 'Non-WM Hypointensities Norm Min',
        'non_wm_hypointensities_normmax': 'Non-WM Hypointensities Norm Max',
        'non_wm_hypointensities_normrange': 'Non-WM Hypointensities Norm Range',
        'left_non_wm_hypointensities_volume_mm3': 'Left Non-WM Hypointensities Volume (mm3)',
        'left_non_wm_hypointensities_normmean': 'Left Non-WM Hypointensities Norm Mean',
        'left_non_wm_hypointensities_normstddev': 'Left Non-WM Hypointensities Norm Std Dev',
        'left_non_wm_hypointensities_normmin': 'Left Non-WM Hypointensities Norm Min',
        'left_non_wm_hypointensities_normmax': 'Left Non-WM Hypointensities Norm Max',
        'left_non_wm_hypointensities_normrange': 'Left Non-WM Hypointensities Norm Range',
        'right_non_wm_hypointensities_volume_mm3': 'Right Non-WM Hypointensities Volume (mm3)',
        'right_non_wm_hypointensities_normmean': 'Right Non-WM Hypointensities Norm Mean',
        'right_non_wm_hypointensities_normstddev': 'Right Non-WM Hypointensities Norm Std Dev',
        'right_non_wm_hypointensities_normmin': 'Right Non-WM Hypointensities Norm Min',
        'right_non_wm_hypointensities_normmax': 'Right Non-WM Hypointensities Norm Max',
        'right_non_wm_hypointensities_normrange': 'Right Non-WM Hypointensities Norm Range',
        'optic_chiasm_volume_mm3': 'Optic Chiasm Volume (mm3)',
        'optic_chiasm_normmean': 'Optic Chiasm Norm Mean',
        'optic_chiasm_normstddev': 'Optic Chiasm Norm Std Dev',
        'optic_chiasm_normmin': 'Optic Chiasm Norm Min',
        'optic_chiasm_normmax': 'Optic Chiasm Norm Max',
        'optic_chiasm_normrange': 'Optic Chiasm Norm Range',
        'cc_posterior_volume_mm3': 'CC Posterior Volume (mm3)',
        'cc_posterior_normmean': 'CC Posterior Norm Mean',
        'cc_posterior_normstddev': 'CC Posterior Norm Std Dev',
        'cc_posterior_normmin': 'CC Posterior Norm Min',
        'cc_posterior_normmax': 'CC Posterior Norm Max',
        'cc_posterior_normrange': 'CC Posterior Norm Range',
        'cc_mid_posterior_volume_mm3': 'CC Mid Posterior Volume (mm3)',
        'cc_mid_posterior_normmean': 'CC Mid Posterior Norm Mean',
        'cc_mid_posterior_normstddev': 'CC Mid Posterior Norm Std Dev',
        'cc_mid_posterior_normmin': 'CC Mid Posterior Norm Min',
        'cc_mid_posterior_normmax': 'CC Mid Posterior Norm Max',
        'cc_mid_posterior_normrange': 'CC Mid Posterior Norm Range',
        'cc_central_volume_mm3': 'CC Central Volume (mm3)',
        'cc_central_normmean': 'CC Central Norm Mean',
        'cc_central_normstddev': 'CC Central Norm Std Dev',
        'cc_central_normmin': 'CC Central Norm Min',
        'cc_central_normmax': 'CC Central Norm Max',
        'cc_central_normrange': 'CC Central Norm Range',
        'cc_mid_anterior_volume_mm3': 'CC Mid Anterior Volume (mm3)',
        'cc_mid_anterior_normmean': 'CC Mid Anterior Norm Mean',
        'cc_mid_anterior_normstddev': 'CC Mid Anterior Norm Std Dev',
        'cc_mid_anterior_normmin': 'CC Mid Anterior Norm Min',
        'cc_mid_anterior_normmax': 'CC Mid Anterior Norm Max',
        'cc_mid_anterior_normrange': 'CC Mid Anterior Norm Range',
        'cc_anterior_volume_mm3': 'CC Anterior Volume (mm3)',
        'cc_anterior_normmean': 'CC Anterior Norm Mean',
        'cc_anterior_normstddev': 'CC Anterior Norm Std Dev',
        'cc_anterior_normmin': 'CC Anterior Norm Min',
        'cc_anterior_normmax': 'CC Anterior Norm Max',
        'cc_anterior_normrange': 'CC Anterior Norm Range'
    }
    return attribute_mapping.get(attribute_name, attribute_name)

def create_freesurfer_sonuc(muayene, row):
    return FreeSurferSonuc.objects.create(
        muayene=muayene,
        diagnosis =row.get('Diagnosis'),
        brain_seg_vol =row.get('BrainSegVol'),
        brain_seg_vol_not_vent =row.get('BrainSegVolNotVent'),
        ventricle_choroid_vol =row.get('VentricleChoroidVol'),
        lh_cortex_vol =row.get('lhCortexVol'),
        rh_cortex_vol =row.get('rhCortexVol'),
        cortex_vol =row.get('CortexVol'),
        lh_cerebral_white_matter_vol=row.get('lhCerebralWhiteMatterVol'),
        rh_cerebral_white_matter_vol=row.get('rhCerebralWhiteMatterVol'),
        cerebral_white_matter_vol=row.get('CerebralWhiteMatterVol'),
        subcort_gray_vol=row.get('SubCortGrayVol'),
        total_gray_vol=row.get('TotalGrayVol'),
        supra_tentorial_vol=row.get('SupraTentorialVol'),
        supra_tentorial_vol_not_vent=row.get('SupraTentorialVolNotVent'),
        mask_vol=row.get('MaskVol'),
        brain_seg_vol_to_etiv=row.get('BrainSegVol-to-eTIV'),
        mask_vol_to_etiv=row.get('MaskVol-to-eTIV'),
        lh_surface_holes=row.get('lhSurfaceHoles'),
        rh_surface_holes=row.get('rhSurfaceHoles'),
        surface_holes=row.get('SurfaceHoles'),
        etiv=row.get('eTIV'),
        left_lateral_ventricle_volume_mm3=row.get('Left-Lateral-Ventricle_Volume_mm3'),
        left_lateral_ventricle_normmean=row.get('Left-Lateral-Ventricle_normMean'),
        left_lateral_ventricle_normstddev=row.get('Left-Lateral-Ventricle_normStdDev'),
        left_lateral_ventricle_normmin=row.get('Left-Lateral-Ventricle_normMin'),
        left_lateral_ventricle_normmax=row.get('Left-Lateral-Ventricle_normMax'),
        left_lateral_ventricle_normrange=row.get('Left-Lateral-Ventricle_normRange'),
        left_inf_lat_vent_volume_mm3=row.get('Left-Inf-Lat-Vent_Volume_mm3'),
        left_inf_lat_vent_normmean=row.get('Left-Inf-Lat-Vent_normMean'),
        left_inf_lat_vent_normstddev=row.get('Left-Inf-Lat-Vent_normStdDev'),
        left_inf_lat_vent_normmin=row.get('Left-Inf-Lat-Vent_normMin'),
        left_inf_lat_vent_normmax=row.get('Left-Inf-Lat-Vent_normMax'),
        left_inf_lat_vent_normrange=row.get('Left-Inf-Lat-Vent_normRange'),
        left_cerebellum_white_matter_volume_mm3=row.get('Left-Cerebellum-White-Matter_Volume_mm3'),
        left_cerebellum_white_matter_normmean=row.get('Left-Cerebellum-White-Matter_normMean'),
        left_cerebellum_white_matter_normstddev=row.get('Left-Cerebellum-White-Matter_normStdDev'),
        left_cerebellum_white_matter_normmin=row.get('Left-Cerebellum-White-Matter_normMin'),
        left_cerebellum_white_matter_normmax=row.get('Left-Cerebellum-White-Matter_normMax'),
        left_cerebellum_white_matter_normrange=row.get('Left-Cerebellum-White-Matter_normRange'),
        left_cerebellum_cortex_volume_mm3=row.get('Left-Cerebellum-Cortex_Volume_mm3'),
        left_cerebellum_cortex_normmean=row.get('Left-Cerebellum-Cortex_normMean'),
        left_cerebellum_cortex_normstddev=row.get('Left-Cerebellum-Cortex_normStdDev'),
        left_cerebellum_cortex_normmin=row.get('Left-Cerebellum-Cortex_normMin'),
        left_cerebellum_cortex_normmax=row.get('Left-Cerebellum-Cortex_normMax'),
        left_cerebellum_cortex_normrange=row.get('Left-Cerebellum-Cortex_normRange'),
        left_thalamus_volume_mm3=row.get('Left-Thalamus_Volume_mm3'),
        left_thalamus_normmean=row.get('Left-Thalamus_normMean'),
        left_thalamus_normstddev=row.get('Left-Thalamus_normStdDev'),
        left_thalamus_normmin=row.get('Left-Thalamus_normMin'),
        left_thalamus_normmax=row.get('Left-Thalamus_normMax'),
        left_thalamus_normrange=row.get('Left-Thalamus_normRange'),
        left_caudate_volume_mm3=row.get('Left-Caudate_Volume_mm3'),
        left_caudate_normmean=row.get('Left-Caudate_normMean'),
        left_caudate_normstddev=row.get('Left-Caudate_normStdDev'),
        left_caudate_normmin=row.get('Left-Caudate_normMin'),
        left_caudate_normmax=row.get('Left-Caudate_normMax'),
        left_caudate_normrange=row.get('Left-Caudate_normRange'),
        left_putamen_volume_mm3=row.get('Left-Putamen_Volume_mm3'),
        left_putamen_normmean=row.get('Left-Putamen_normMean'),
        left_putamen_normstddev=row.get('Left-Putamen_normStdDev'),
        left_putamen_normmin=row.get('Left-Putamen_normMin'),
        left_putamen_normmax=row.get('Left-Putamen_normMax'),
        left_putamen_normrange=row.get('Left-Putamen_normRange'),
        left_pallidum_volume_mm3=row.get('Left-Pallidum_Volume_mm3'),
        left_pallidum_normmean=row.get('Left-Pallidum_normMean'),
        left_pallidum_normstddev=row.get('Left-Pallidum_normStdDev'),
        left_pallidum_normmin=row.get('Left-Pallidum_normMin'),
        left_pallidum_normmax=row.get('Left-Pallidum_normMax'),
        left_pallidum_normrange=row.get('Left-Pallidum_normRange'),
        the3rd_ventricle_volume_mm3=row.get('3rd-Ventricle_Volume_mm3'),
        the3rd_ventricle_normmean=row.get('3rd-Ventricle_normMean'),
        the3rd_ventricle_normstddev=row.get('3rd-Ventricle_normStdDev'),
        the3rd_ventricle_normmax=row.get('3rd-Ventricle_normMax'),
        the3rd_ventricle_normrange=row.get('3rd-Ventricle_normRange'),
        the3rd_ventricle_normmin=row.get('3rd-Ventricle_normMin'),
        the4th_ventricle_volume_mm3=row.get('4th-Ventricle_Volume_mm3'),
        the4th_ventricle_normmean=row.get('4th-Ventricle_normMean'),
        the4th_ventricle_normstddev=row.get('4th-Ventricle_normStdDev'),
        the4th_ventricle_normmin=row.get('4th-Ventricle_normMin'),
        the4th_ventricle_normmax=row.get('4th-Ventricle_normMax'),
        the4th_ventricle_normrange=row.get('4th-Ventricle_normRange'),
        brain_stem_volume_mm3=row.get('Brain-Stem_Volume_mm3'),
        brain_stem_normmean=row.get('Brain-Stem_normMean'),
        brain_stem_normstddev=row.get('Brain-Stem_normStdDev'),
        brain_stem_normmin=row.get('Brain-Stem_normMin'),
        brain_stem_normmax=row.get('Brain-Stem_normMax'),
        brain_stem_normrange=row.get('Brain-Stem_normRange'),
        left_hippocampus_volume_mm3=row.get('Left-Hippocampus_Volume_mm3'),
        left_hippocampus_normmean=row.get('Left-Hippocampus_normMean'),
        left_hippocampus_normstddev=row.get('Left-Hippocampus_normStdDev'),
        left_hippocampus_normmin=row.get('Left-Hippocampus_normMin'),
        left_hippocampus_normmax=row.get('Left-Hippocampus_normMax'),
        left_hippocampus_normrange=row.get('Left-Hippocampus_normRange'),
        left_amygdala_volume_mm3=row.get('Left-Amygdala_Volume_mm3'),
        left_amygdala_normmean=row.get('Left-Amygdala_normMean'),
        left_amygdala_normstddev=row.get('Left-Amygdala_normStdDev'),
        left_amygdala_normmin=row.get('Left-Amygdala_normMin'),
        left_amygdala_normmax=row.get('Left-Amygdala_normMax'),
        left_amygdala_normrange=row.get('Left-Amygdala_normRange'),
        csf_volume_mm3=row.get('CSF_Volume_mm3'),
        csf_normmean=row.get('CSF_normMean'),
        csf_normstddev=row.get('CSF_normStdDev'),
        csf_normmin=row.get('CSF_normMin'),
        csf_normmax=row.get('CSF_normMax'),
        csf_normrange=row.get('CSF_normRange'),
        left_accumbens_area_volume_mm3=row.get('Left-Accumbens-area_Volume_mm3'),
        left_accumbens_area_normmean=row.get('Left-Accumbens-area_normMean'),
        left_accumbens_area_normstddev=row.get('Left-Accumbens-area_normStdDev'),
        left_accumbens_area_normmin=row.get('Left-Accumbens-area_normMin'),
        left_accumbens_area_normmax=row.get('Left-Accumbens-area_normMax'),
        left_accumbens_area_normrange=row.get('Left-Accumbens-area_normRange'),
        left_ventraldc_volume_mm3=row.get('Left-VentralDC_Volume_mm3'),
        left_ventraldc_normmean=row.get('Left-VentralDC_normMean'),
        left_ventraldc_normstddev=row.get('Left-VentralDC_normStdDev'),
        left_ventraldc_normmin=row.get('Left-VentralDC_normMin'),
        left_ventraldc_normmax=row.get('Left-VentralDC_normMax'),
        left_ventraldc_normrange=row.get('Left-VentralDC_normRange'),
        left_vessel_volume_mm3=row.get('Left-vessel_Volume_mm3'),
        left_vessel_normmean=row.get('Left-vessel_normMean'),
        left_vessel_normstddev=row.get('Left-vessel_normStdDev'),
        left_vessel_normmin=row.get('Left-vessel_normMin'),
        left_vessel_normmax=row.get('Left-vessel_normMax'),
        left_vessel_normrange=row.get('Left-vessel_normRange'),
        left_choroid_plexus_volume_mm3=row.get('Left-choroid-plexus_Volume_mm3'),
        left_choroid_plexus_normmean=row.get('Left-choroid-plexus_normMean'),
        left_choroid_plexus_normstddev=row.get('Left-choroid-plexus_normStdDev'),
        left_choroid_plexus_normmin=row.get('Left-choroid-plexus_normMin'),
        left_choroid_plexus_normmax=row.get('Left-choroid-plexus_normMax'),
        left_choroid_plexus_normrange=row.get('Left-choroid-plexus_normRange'),
        right_lateral_ventricle_volume_mm3=row.get('Right-Lateral-Ventricle_Volume_mm3'),
        right_lateral_ventricle_normmean=row.get('Right-Lateral-Ventricle_normMean'),
        right_lateral_ventricle_normstddev=row.get('Right-Lateral-Ventricle_normStdDev'),
        right_lateral_ventricle_normmin=row.get('Right-Lateral-Ventricle_normMin'),
        right_lateral_ventricle_normmax=row.get('Right-Lateral-Ventricle_normMax'),
        right_lateral_ventricle_normrange=row.get('Right-Lateral-Ventricle_normRange'),
        right_inf_lat_vent_volume_mm3=row.get('Right-Inf-Lat-Vent_Volume_mm3'),
        right_inf_lat_vent_normmean=row.get('Right-Inf-Lat-Vent_normMean'),
        right_inf_lat_vent_normstddev=row.get('Right-Inf-Lat-Vent_normStdDev'),
        right_inf_lat_vent_normmin=row.get('Right-Inf-Lat-Vent_normMin'),
        right_inf_lat_vent_normmax=row.get('Right-Inf-Lat-Vent_normMax'),
        right_inf_lat_vent_normrange=row.get('Right-Inf-Lat-Vent_normRange'),
        right_cerebellum_white_matter_volume_mm3=row.get('Right-Cerebellum-White-Matter_Volume_mm3'),
        right_cerebellum_white_matter_normmean=row.get('Right-Cerebellum-White-Matter_normMean'),
        right_cerebellum_white_matter_normstddev=row.get('Right-Cerebellum-White-Matter_normStdDev'),
        right_cerebellum_white_matter_normmin=row.get('Right-Cerebellum-White-Matter_normMin'),
        right_cerebellum_white_matter_normmax=row.get('Right-Cerebellum-White-Matter_normMax'),
        right_cerebellum_white_matter_normrange=row.get('Right-Cerebellum-White-Matter_normRange'),
        right_cerebellum_cortex_volume_mm3=row.get('Right-Cerebellum-Cortex_Volume_mm3'),
        right_cerebellum_cortex_normmean=row.get('Right-Cerebellum-Cortex_normMean'),
        right_cerebellum_cortex_normstddev=row.get('Right-Cerebellum-Cortex_normStdDev'),
        right_cerebellum_cortex_normmin=row.get('Right-Cerebellum-Cortex_normMin'),
        right_cerebellum_cortex_normmax=row.get('Right-Cerebellum-Cortex_normMax'),
        right_cerebellum_cortex_normrange=row.get('Right-Cerebellum-Cortex_normRange'),
        right_thalamus_volume_mm3=row.get('Right-Thalamus_Volume_mm3'),
        right_thalamus_normmean=row.get('Right-Thalamus_normMean'),
        right_thalamus_normstddev=row.get('Right-Thalamus_normStdDev'),
        right_thalamus_normmin=row.get('Right-Thalamus_normMin'),
        right_thalamus_normmax=row.get('Right-Thalamus_normMax'),
        right_thalamus_normrange=row.get('Right-Thalamus_normRange'),
        right_caudate_volume_mm3=row.get('Right-Caudate_Volume_mm3'),
        right_caudate_normmean=row.get('Right-Caudate_normMean'),
        right_caudate_normstddev=row.get('Right-Caudate_normStdDev'),
        right_caudate_normmin=row.get('Right-Caudate_normMin'),
        right_caudate_normmax=row.get('Right-Caudate_normMax'),
        right_caudate_normrange=row.get('Right-Caudate_normRange'),
        right_putamen_volume_mm3=row.get('Right-Putamen_Volume_mm3'),
        right_putamen_normmean=row.get('Right-Putamen_normMean'),
        right_putamen_normstddev=row.get('Right-Putamen_normStdDev'),
        right_putamen_normmin=row.get('Right-Putamen_normMin'),
        right_putamen_normmax=row.get('Right-Putamen_normMax'),
        right_putamen_normrange=row.get('Right-Putamen_normRange'),
        right_pallidum_volume_mm3=row.get('Right-Pallidum_Volume_mm3'),
        right_pallidum_normmean=row.get('Right-Pallidum_normMean'),
        right_pallidum_normstddev=row.get('Right-Pallidum_normStdDev'),
        right_pallidum_normmin=row.get('Right-Pallidum_normMin'),
        right_pallidum_normmax=row.get('Right-Pallidum_normMax'),
        right_pallidum_normrange=row.get('Right-Pallidum_normRange'),
        right_hippocampus_volume_mm3=row.get('Right-Hippocampus_Volume_mm3'),
        right_hippocampus_normmean=row.get('Right-Hippocampus_normMean'),
        right_hippocampus_normstddev=row.get('Right-Hippocampus_normStdDev'),
        right_hippocampus_normmin=row.get('Right-Hippocampus_normMin'),
        right_hippocampus_normmax=row.get('Right-Hippocampus_normMax'),
        right_hippocampus_normrange=row.get('Right-Hippocampus_normRange'),
        right_amygdala_volume_mm3=row.get('Right-Amygdala_Volume_mm3'),
        right_amygdala_normmean=row.get('Right-Amygdala_normMean'),
        right_amygdala_normstddev=row.get('Right-Amygdala_normStdDev'),
        right_amygdala_normmin=row.get('Right-Amygdala_normMin'),
        right_amygdala_normmax=row.get('Right-Amygdala_normMax'),
        right_amygdala_normrange=row.get('Right-Amygdala_normRange'),
        right_accumbens_area_volume_mm3=row.get('Right-Accumbens-area_Volume_mm3'),
        right_accumbens_area_normmean=row.get('Right-Accumbens-area_normMean'),
        right_accumbens_area_normstddev=row.get('Right-Accumbens-area_normStdDev'),
        right_accumbens_area_normmin=row.get('Right-Accumbens-area_normMin'),
        right_accumbens_area_normmax=row.get('Right-Accumbens-area_normMax'),
        right_accumbens_area_normrange=row.get('Right-Accumbens-area_normRange'),
        right_ventraldc_volume_mm3=row.get('Right-VentralDC_Volume_mm3'),
        right_ventraldc_normmean=row.get('Right-VentralDC_normMean'),
        right_ventraldc_normstddev=row.get('Right-VentralDC_normStdDev'),
        right_ventraldc_normmin=row.get('Right-VentralDC_normMin'),
        right_ventraldc_normmax=row.get('Right-VentralDC_normMax'),
        right_ventraldc_normrange=row.get('Right-VentralDC_normRange'),
        right_vessel_volume_mm3=row.get('Right-vessel_Volume_mm3'),
        right_vessel_normmean=row.get('Right-vessel_normMean'),
        right_vessel_normstddev=row.get('Right-vessel_normStdDev'),
        right_vessel_normmin=row.get('Right-vessel_normMin'),
        right_vessel_normmax=row.get('Right-vessel_normMax'),
        right_vessel_normrange=row.get('Right-vessel_normRange'),
        right_choroid_plexus_volume_mm3=row.get('Right-choroid-plexus_Volume_mm3'),
        right_choroid_plexus_normmean=row.get('Right-choroid-plexus_normMean'),
        right_choroid_plexus_normstddev=row.get('Right-choroid-plexus_normStdDev'),
        right_choroid_plexus_normmin=row.get('Right-choroid-plexus_normMin'),
        right_choroid_plexus_normmax=row.get('Right-choroid-plexus_normMax'),
        right_choroid_plexus_normrange=row.get('Right-choroid-plexus_normRange'),
        the5th_ventricle_volume_mm3=row.get('5th-Ventricle_Volume_mm3'),
        the5th_ventricle_normmean=row.get('5th-Ventricle_normMean'),
        the5th_ventricle_normstddev=row.get('5th-Ventricle_normStdDev'),
        the5th_ventricle_normmin=row.get('5th-Ventricle_normMin'),
        the5th_ventricle_normmax=row.get('5th-Ventricle_normMax'),
        the5th_ventricle_normrange=row.get('5th-Ventricle_normRange'),
        wm_hypointensities_volume_mm3=row.get('WM-hypointensities_Volume_mm3'),
        wm_hypointensities_normmean=row.get('WM-hypointensities_normMean'),
        wm_hypointensities_normstddev=row.get('WM-hypointensities_normStdDev'),
        wm_hypointensities_normmin=row.get('WM-hypointensities_normMin'),
        wm_hypointensities_normmax=row.get('WM-hypointensities_normMax'),
        wm_hypointensities_normrange=row.get('WM-hypointensities_normRange'),
        left_wm_hypointensities_volume_mm3=row.get('Left-WM-hypointensities_Volume_mm3'),
        left_wm_hypointensities_normmean=row.get('Left-WM-hypointensities_normMean'),
        left_wm_hypointensities_normstddev=row.get('Left-WM-hypointensities_normStdDev'),
        left_wm_hypointensities_normmin=row.get('Left-WM-hypointensities_normMin'),
        left_wm_hypointensities_normmax=row.get('Left-WM-hypointensities_normMax'),
        left_wm_hypointensities_normrange=row.get('Left-WM-hypointensities_normRange'),
        right_wm_hypointensities_volume_mm3=row.get('Right-WM-hypointensities_Volume_mm3'),
        right_wm_hypointensities_normmean=row.get('Right-WM-hypointensities_normMean'),
        right_wm_hypointensities_normstddev=row.get('Right-WM-hypointensities_normStdDev'),
        right_wm_hypointensities_normmin=row.get('Right-WM-hypointensities_normMin'),
        right_wm_hypointensities_normmax=row.get('Right-WM-hypointensities_normMax'),
        right_wm_hypointensities_normrange=row.get('Right-WM-hypointensities_normRange'),
        non_wm_hypointensities_volume_mm3=row.get('non-WM-hypointensities_Volume_mm3'),
        non_wm_hypointensities_normmean=row.get('non-WM-hypointensities_normMean'),
        non_wm_hypointensities_normstddev=row.get('non-WM-hypointensities_normStdDev'),
        non_wm_hypointensities_normmin=row.get('non-WM-hypointensities_normMin'),
        non_wm_hypointensities_normmax=row.get('non-WM-hypointensities_normMax'),
        non_wm_hypointensities_normrange=row.get('non-WM-hypointensities_normRange'),
        left_non_wm_hypointensities_volume_mm3=row.get('Left-non-WM-hypointensities_Volume_mm3'),
        left_non_wm_hypointensities_normmean=row.get('Left-non-WM-hypointensities_normMean'),
        left_non_wm_hypointensities_normstddev=row.get('Left-non-WM-hypointensities_normStdDev'),
        left_non_wm_hypointensities_normmin=row.get('Left-non-WM-hypointensities_normMin'),
        left_non_wm_hypointensities_normmax=row.get('Left-non-WM-hypointensities_normMax'),
        left_non_wm_hypointensities_normrange=row.get('Left-non-WM-hypointensities_normRange'),
        right_non_wm_hypointensities_volume_mm3=row.get('Right-non-WM-hypointensities_Volume_mm3'),
        right_non_wm_hypointensities_normmean=row.get('Right-non-WM-hypointensities_normMean'),
        right_non_wm_hypointensities_normstddev=row.get('Right-non-WM-hypointensities_normStdDev'),
        right_non_wm_hypointensities_normmin=row.get('Right-non-WM-hypointensities_normMin'),
        right_non_wm_hypointensities_normmax=row.get('Right-non-WM-hypointensities_normMax'),
        right_non_wm_hypointensities_normrange=row.get('Right-non-WM-hypointensities_normRange'),
        optic_chiasm_volume_mm3=row.get('Optic-Chiasm_Volume_mm3'),
        optic_chiasm_normmean=row.get('Optic-Chiasm_normMean'),
        optic_chiasm_normstddev=row.get('Optic-Chiasm_normStdDev'),
        optic_chiasm_normmin=row.get('Optic-Chiasm_normMin'),
        optic_chiasm_normmax=row.get('Optic-Chiasm_normMax'),
        optic_chiasm_normrange=row.get('Optic-Chiasm_normRange'),
        cc_posterior_volume_mm3=row.get('CC_Posterior_Volume_mm3'),
        cc_posterior_normmean=row.get('CC_Posterior_normMean'),
        cc_posterior_normstddev=row.get('CC_Posterior_normStdDev'),
        cc_posterior_normmin=row.get('CC_Posterior_normMin'),
        cc_posterior_normmax=row.get('CC_Posterior_normMax'),
        cc_posterior_normrange=row.get('CC_Posterior_normRange'),
        cc_mid_posterior_volume_mm3=row.get('CC_Mid_Posterior_Volume_mm3'),
        cc_mid_posterior_normmean=row.get('CC_Mid_Posterior_normMean'),
        cc_mid_posterior_normstddev=row.get('CC_Mid_Posterior_normStdDev'),
        cc_mid_posterior_normmin=row.get('CC_Mid_Posterior_normMin'),
        cc_mid_posterior_normmax=row.get('CC_Mid_Posterior_normMax'),
        cc_mid_posterior_normrange=row.get('CC_Mid_Posterior_normRange'),
        cc_central_volume_mm3=row.get('CC_Central_Volume_mm3'),
        cc_central_normmean=row.get('CC_Central_normMean'),
        cc_central_normstddev=row.get('CC_Central_normStdDev'),
        cc_central_normmin=row.get('CC_Central_normMin'),
        cc_central_normmax=row.get('CC_Central_normMax'),
        cc_central_normrange=row.get('CC_Central_normRange'),
        cc_mid_anterior_volume_mm3=row.get('CC_Mid_Anterior_Volume_mm3'),
        cc_mid_anterior_normmean=row.get('CC_Mid_Anterior_normMean'),
        cc_mid_anterior_normstddev=row.get('CC_Mid_Anterior_normStdDev'),
        cc_mid_anterior_normmin=row.get('CC_Mid_Anterior_normMin'),
        cc_mid_anterior_normmax=row.get('CC_Mid_Anterior_normMax'),
        cc_mid_anterior_normrange=row.get('CC_Mid_Anterior_normRange'),
        cc_anterior_volume_mm3=row.get('CC_Anterior_Volume_mm3'),
        cc_anterior_normmean=row.get('CC_Anterior_normMean'),
        cc_anterior_normstddev=row.get('CC_Anterior_normStdDev'),
        cc_anterior_normmin=row.get('CC_Anterior_normMin'),
        cc_anterior_normmax=row.get('CC_Anterior_normMax'),
        cc_anterior_normrange=row.get('CC_Anterior_normRange')
    )

def process_freesurfer_file(file, muayene):
    try:
        # Excel dosyasını oku
        df = pd.read_excel(file)

        # Her bir satırı al ve FreeSurferSonuc tablosuna ekle
        for _, row in df.iterrows():
            create_freesurfer_sonuc(muayene, row)
                
        print(f"Successfully processed and saved {len(df)} FreeSurfer rows for Muayene {muayene.id}")
        FreeSurferSonuc.save()

    except Exception as e:
        print(f"Error processing FreeSurfer file: {e}")

selected_columns = []
def freesurfer_list_view(request):
    global selected_columns
    tanilar = FreeSurferSonuc.objects.values_list('diagnosis', flat=True).distinct()
     # Dynamically get all fields from the model
    all_fields = [field.name for field in FreeSurferSonuc._meta.get_fields()]

    if request.GET.get('reset'):
        selected_tani = 'Tüm Tanılar'
        selected_hasta_id = ''
        selected_columns = []
        columns = [{"field": field, "label": get_pretty_attribute_name(field)} for field in all_fields]
        print("Resetting filters")
    else:
        selected_tani = request.GET.get('tani', 'Tüm Tanılar')
        selected_hasta_id = request.GET.get('hasta_id')
        print(selected_hasta_id)

        added_columns = request.GET.getlist('columns')

        # Sadece mevcut olmayanları ekle
        for column in added_columns:
            if column not in selected_columns:
                selected_columns.append(column)
        

    filters = {}
    if selected_tani and selected_tani != 'Tüm Tanılar':
        filters['diagnosis'] = selected_tani
    if selected_hasta_id and selected_hasta_id != '':
        filters['muayene__hasta__hasta_id'] = selected_hasta_id

    freesurfer_sonuclari = FreeSurferSonuc.objects.filter(**filters)
    
    # Map each field to a pretty label (using your existing function or a mapping)
    columns = [{"field": field, "label": get_pretty_attribute_name(field)} for field in all_fields]
    static_columns = [{"field": field, "label": get_pretty_attribute_name(field)} for field in all_fields]

    if (len(selected_columns) > 0):
        converted_columns = []
        for column_str in selected_columns:
            try:
                # Convert the string to a dictionary
                column_dict = ast.literal_eval(column_str)
                if isinstance(column_dict, dict):  # Ensure it's a dictionary
                    converted_columns.append(column_dict)  # Append the dictionary to the list
            except (SyntaxError, ValueError) as e:
                print(f"Invalid column string: {column_str} - Error: {e}")
        columns = columns[:2] + converted_columns

    statistics = {}
    if request.method == "POST":
        numeric_attributes = [
            field.name for field in FreeSurferSonuc._meta.fields 
            if isinstance(field, (models.DecimalField))
        ]
        for attribute in numeric_attributes:
            values = freesurfer_sonuclari.values_list(attribute, flat=True)
            filtered_values = [v for v in values if v is not None]
            if filtered_values:
                mean = round(np.mean(filtered_values), 2)
                stddev = round(np.std(filtered_values), 2)
                statistics[attribute] = {'mean': mean, 'stddev': stddev}

    pretty_statistics = {get_pretty_attribute_name(attr): stats for attr, stats in statistics.items()}

    return render(request, 'freesurfer_list.html', {
        'freesurfer_sonuclari': freesurfer_sonuclari,
        'columns': columns,
        'static_columns': static_columns,
        'tanilar': tanilar,
        'selected_tani': selected_tani,
        'selected_hasta_id': selected_hasta_id,
        'selected_columns': selected_columns,
        'statistics': pretty_statistics
    })

def export_freesurfer_to_excel(request):
    global selected_columns
     # Dynamically get all fields from the model
    all_fields = [field.name for field in FreeSurferSonuc._meta.get_fields()]

    selected_tani = request.POST.get('tani') or request.GET.get('tani') or 'Tüm Tanılar'
    selected_hasta_id = request.POST.get('hasta_id') or request.GET.get('hasta_id') or ''

    filters = {}
    if selected_tani and selected_tani != 'Tüm Tanılar':
        filters['diagnosis'] = selected_tani
    if selected_hasta_id and selected_hasta_id != '':
        filters['muayene__hasta__hasta_id'] = selected_hasta_id

    freesurfer_sonuclari = FreeSurferSonuc.objects.filter(**filters)

    if selected_columns:
        # Prepare the selected columns to include in the export
        columns_to_export = []
        for column_str in selected_columns:
            try:
                # Convert the string to a dictionary
                column_dict = ast.literal_eval(column_str)
                if isinstance(column_dict, dict):
                    field = column_dict.get("field")
                    if field:
                        # Get the pretty display name for the field
                        pretty_name = get_pretty_attribute_name(field)
                        columns_to_export.append({
                            'field': field,
                            'label': pretty_name
                        })
            except (SyntaxError, ValueError) as e:
                print(f"Invalid column string: {column_str} - Error: {e}")

        # Only keep the rows and columns that match the selected columns
        data = []
        for sonuc in freesurfer_sonuclari:
            row = {}
            for column in columns_to_export:
                field = column['field']
                row[column['label']] = getattr(sonuc, field)
            data.append(row)
    else:
        # If no selected columns, export all columns
        data = []
        all_fields = [field.name for field in FreeSurferSonuc._meta.get_fields()]
        for sonuc in freesurfer_sonuclari:
            row = {}
            for field in all_fields:
                pretty_name = get_pretty_attribute_name(field)
                row[pretty_name] = getattr(sonuc, field)
            data.append(row)

    # Create a DataFrame for the data
    df = pd.DataFrame(data)

    # Create an Excel response
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="freesurfer_sonuclari.xlsx"'
    df.to_excel(response, index=False)

    return response

def safe_integer(value):
    """Convert value to integer if possible, otherwise return None for NaN or invalid values."""
    if pd.isna(value):  # Checks for NaN
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def upload_bulk_data_view(request):
    if request.method == 'POST':
        if 'bulk_mri_submit' in request.POST:
            mri_file = request.FILES.get('bulk_mri_file')
            if not mri_file:
                return HttpResponse("No MRI file uploaded", status=400)

            try:
                df = pd.read_excel(mri_file)
                print("MRI file read successfully.")
            except Exception as e:
                print(f"Error reading MRI file: {e}")
                return HttpResponse(f"Error reading MRI file: {e}", status=400)

            for _, row in df.iterrows():
                id = row.get('Patient_ID')
                try:
                    hasta = Hasta.objects.get(hasta_id=id)
                except Hasta.DoesNotExist:
                    print(f"Hasta ID {id} not found, skipping.")
                    continue  
                
                muayene = Muayene.objects.create(hasta=hasta)
                create_freesurfer_sonuc(muayene, row)

            return render(request, 'bulk_data_upload.html', {'message': 'MRI data uploaded successfully.'})

        elif 'bulk_visit_submit' in request.POST:
            bulk_file = request.FILES.get('visit_file')
            if not bulk_file:
                return HttpResponse("No Visit file uploaded", status=400)

            try:
                df = pd.read_excel(bulk_file)
                print("Visit file read successfully.")
            except Exception as e:
                print(f"Error reading Visit file: {e}")
                return HttpResponse(f"Error reading Visit file: {e}", status=400)
            
            for _, row in df.iterrows():
                # Extract patient details
                full_name = row.get('Hasta İsim')
                if full_name:
                    name_parts = full_name.split()
                    patient_surname = name_parts[-1]
                    patient_name = " ".join(name_parts[:-1])
                else:
                    continue

                education_status = row.get('Eğitim durumu') if pd.notna(row.get('Eğitim durumu')) else 'Unknown'
                city = row.get('Yaşadığı şehir') if pd.notna(row.get('Yaşadığı şehir')) else 'Unknown'
                marital_status = row.get('Medeni hal') if pd.notna(row.get('Medeni hal')) else 'Unknown'
                gender = row.get('Cinsiyet') if pd.notna(row.get('Cinsiyet')) else 'Unknown'
                occupation = row.get('Meslek') if pd.notna(row.get('Meslek')) else 'Unknown'
                age = int(row.get('Yaş')) if pd.notna(row.get('Yaş')) else -1

                try:
                    patient = Hasta.objects.get(
                        isim=patient_name,
                        soyisim=patient_surname,
                        egitim_durumu=education_status,
                        sehir=city,
                        medeni_durum=marital_status,
                        cinsiyet=gender,
                        meslek=occupation,
                        yas=age,
                    )
                except Hasta.DoesNotExist:
                    patient = Hasta.objects.create(
                        isim=patient_name,
                        soyisim=patient_surname,
                        egitim_durumu=education_status,
                        sehir=city,
                        medeni_durum=marital_status,
                        cinsiyet=gender,
                        yas=age,
                        meslek=occupation
                    )

                # Date handling for visit_date and encryption
                encrypted_date = None
                day = row.get('(Gerçek) Ziyaret tarihi (gün)')
                month = row.get('(Gerçek) Ziyaret tarihi (ay)')
                year = row.get('(Gerçek) Ziyaret tarihi (yıl)')

                if pd.notna(day) and pd.notna(month) and pd.notna(year):
                    try:
                        visit_date = datetime(year=int(year), month=int(month), day=int(day))
                        encrypted_date = encrypt(visit_date.strftime('%Y-%m-%d %H:%M:%S'))
                    except ValueError as e:
                        print(f"Error parsing date for row {row}: {e}")

                # Fetch and normalize examination data
                denge_bozuklugu_text = row.get('Denge bozukluğu var mı?', '')
                serebellar_bulgular_text = row.get('Serebellar bulgular var mı?', '')
                ense_sertligi_text = row.get('Ense sertliği var mı?', '')
                parkinsonizm_text = row.get('Parkinsonizm bulguları var mı?', '')
                kranial_sinir_bulgulari_text = row.get('Kranial sinir bulguları var mı?', '')
                motor_duygusal_bulgular_text = row.get('Motor ve duysal bulgular', '')
                patolojik_refleks_text = row.get('Patolojik refleks var mı?', '')

                # Create Muayene record
                muayene = Muayene.objects.create(
                    hasta=patient,
                    sifrelenmis_tarih=encrypted_date,
                    denge_bozuklugu='YOK' not in (denge_bozuklugu_text.upper() if isinstance(denge_bozuklugu_text, str) else ''),
                    serebellar_bulgular='YOK' not in (serebellar_bulgular_text.upper() if isinstance(serebellar_bulgular_text, str) else ''),
                    ense_sertligi='YOK' not in (ense_sertligi_text.upper() if isinstance(ense_sertligi_text, str) else ''),
                    parkinsonizm='YOK' not in (parkinsonizm_text.upper() if isinstance(parkinsonizm_text, str) else ''),
                    kranial_sinir_bulgulari='YOK' not in (kranial_sinir_bulgulari_text.upper() if isinstance(kranial_sinir_bulgulari_text, str) else ''),
                    motor_duygusal_bulgular='YOK' not in (motor_duygusal_bulgular_text.upper() if isinstance(motor_duygusal_bulgular_text, str) else ''),
                    patolojik_refleks='YOK' not in (patolojik_refleks_text.upper() if isinstance(patolojik_refleks_text, str) else ''),
                    mmse=safe_integer(row.get('Mini-Mental State Examination (MMSE) skoru', None)),
                    acer=safe_integer(row.get('Addenbrooke’s Cognitive Examination Revised (ACE-R) skoru', None)),
                    # Add remaining fields here
                )

            return render(request, 'bulk_data_upload.html', {'message': 'Visit data uploaded successfully.'})
    return render(request, 'bulk_data_upload.html')


def new_patient_view(request):
    if request.method == 'POST':
        # Get data from the form
        patient_name = request.POST.get('patient_name')
        patient_surname = request.POST.get('patient_surname')
        education_status = request.POST.get('education_status')
        city = request.POST.get('city')
        marital_status = request.POST.get('medeni')
        gender = request.POST.get('cinsiyet')
        occupation = request.POST.get('meslek')
        age = request.POST.get('patient_age')
        print(f"Name: {patient_name}, Surname: {patient_surname}, Education: {education_status}, City: {city}, Marital Status: {marital_status}, Gender: {gender}")

        # Create a new Hasta instance and save to the database
        new_patient = Hasta(
            isim=patient_name,
            soyisim=patient_surname,
            egitim_durumu=education_status,
            sehir=city,
            medeni_durum=marital_status,
            meslek = occupation,
            cinsiyet=gender,
            yas=age,
        )
        new_patient.save()

        return redirect('home')

    return render(request, 'new_patient.html', {
        'city_options': SEHIR_CHOICES,
        'cinsiyet_options': CINSIYET_CHOICES,  # Pass gender choices
        'medeni_durum_options': MEDENI_DURUM_CHOICES,
        'egitim_durum_options': EGITIM_DURUM_CHOICES 
    })

def search_examination_view(request):
    arama_sonucu = None
    if request.method == "GET":
        arama_kriteri = request.GET.get("arama", "")
        try:
            # Sayısal bir ID girildiyse burada işlenir.
            arama_kriteri_id = int(arama_kriteri)
            arama_sonucu = Muayene.objects.filter(
                Q(hasta__isim__icontains=arama_kriteri) |
                Q(hasta_id=arama_kriteri_id) |
                Q(id=arama_kriteri_id)
            )
        except ValueError:
            # Eğer bir isimle arama yapılmak isteniyorsa buradan devam edilir.
            arama_sonucu = Muayene.objects.filter(
                Q(hasta__isim__icontains=arama_kriteri)
            )
    return render(request, 'search_examination.html', {'arama_sonucu': arama_sonucu})

def edit_examination_view(request, id):
    muayene = get_object_or_404(Muayene, id=id)
    if request.method == 'POST':
        form = MuayeneForm(request.POST, request.FILES, instance=muayene)
        if form.is_valid():
            form.save()
            messages.success(request, 'Muayene başarıyla kaydedildi.')  # Success message
            return redirect('search_examination_view')
    else:
        form = MuayeneForm(instance=muayene)

    return render(request, 'edit_examination.html', {'form': form, 'muayene': muayene})

def patient_detail_view(request, patient_id):
    hasta = get_object_or_404(Hasta, hasta_id=patient_id)
    muayeneler = Muayene.objects.filter(hasta=hasta)
    return render(request, 'patient_detail_view.html', {'hasta': hasta , 'muayeneler': muayeneler})

def data_report_view(request):
    # Gender distribution data
    gender_data = Hasta.objects.values('cinsiyet').annotate(count=Count('cinsiyet'))
    gender_labels = [item['cinsiyet'] for item in gender_data]
    gender_counts = [item['count'] for item in gender_data]

    # Age distribution data (assuming an 'yas' field in Hasta model)
    age_bins = range(0, 100, 10)  # Define age bins (e.g., 0-9, 10-19, ...)
    age_labels = [f"{bin}-{bin + 9}" for bin in age_bins]
    age_counts = [
        Hasta.objects.filter(Q(yas__gte=bin) & Q(yas__lt=bin + 10)).count()
        for bin in age_bins
    ]

    tanilar = FreeSurferSonuc.objects.values('diagnosis').annotate(count=models.Count('diagnosis')).order_by('diagnosis')

    # Tanıların adları ve sayıları
    diagnosis_labels = [t['diagnosis'] for t in tanilar]
    diagnosis_counts = [t['count'] for t in tanilar]

    # Count of patients with MRI data
    patients_with_mri = Hasta.objects.filter(
        muayene__mri_tarihi__isnull=False
    ).distinct().count()

    # Count patients with PET data
    patients_with_pet = Hasta.objects.filter(
        muayene__pet1__isnull=False
    ).distinct().count()

    # Count patients without MRI data
    total_patients = Hasta.objects.count()
    patients_without_mri = total_patients - patients_with_mri
    patients_without_pet = total_patients - patients_with_pet

    return render(request, 'data_report.html', {
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        'age_labels': age_labels,
        'age_counts': age_counts,
        'diagnosis_labels': diagnosis_labels,
        'diagnosis_counts': diagnosis_counts,
        'mri_labels': ['MRI Verisi var', 'MRI Verisi yok'],
        'mri_counts': [patients_with_mri, patients_without_mri],
        'pet_labels': ['PET Verisi var', 'PET Verisi yok'],
        'pet_counts': [patients_with_pet, patients_without_pet]
    })


def download_page(request):
    return render(request, 'download_data_view.html')

# CSV generation helpers
def generate_csv_response(queryset, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([field.name for field in queryset.model._meta.fields])  # Header
    for obj in queryset:
        writer.writerow([getattr(obj, field.name) for field in queryset.model._meta.fields])
    return response

# Separate views for downloading each dataset
def download_hasta_csv(request):
    return generate_csv_response(Hasta.objects.all(), "hasta.csv")

def download_muayene_csv(request):
    return generate_csv_response(Muayene.objects.all(), "muayene.csv")

def download_mri_csv(request):
    return generate_csv_response(FreeSurferSonuc.objects.all(), "mri.csv")

def zero_percentage(vector):
    """Vektördeki sıfır oranını hesaplar."""
    total_elements = len(vector)
    zero_count = vector.count(0)  # Vektördeki sıfır sayısını bul
    return zero_count / total_elements if total_elements > 0 else 0

def patient_similarity_view(request):
    query = request.GET.get('arama', '')
    selected_patient_id = request.GET.get('selected_patient_id', None)
    arama_sonucu = []
    similar_patients = []
    selected_data = None
    similar_data = []
    attribute_labels = []

    if query:
        # Search patients by name or ID
        arama_sonucu = Hasta.objects.filter(
            Q(isim__icontains=query) | 
            Q(soyisim__icontains=query) |
            Q(hasta_id__icontains=query)
        )

    if selected_patient_id:
        try:
            selected_patient_id = int(selected_patient_id)
            selected_patient = Hasta.objects.get(hasta_id=selected_patient_id)

            # Get all patients and scale
            all_patients = list(Hasta.objects.all())
            all_vectors = [patient_to_vector(p) for p in all_patients]
            scaled_all_vectors = scale_vectors(all_vectors)

            # Find selected patient index
            selected_index = next(i for i, p in enumerate(all_patients) if p.hasta_id == selected_patient_id)
            selected_vec = scaled_all_vectors[selected_index]

            # Compute distances
            similarities = []
            for i, p in enumerate(all_patients):
                if p.hasta_id != selected_patient_id:
                    similarity = cosine_similarity(selected_vec, scaled_all_vectors[i])
                    similarities.append((p, similarity))

            # Sort by similarity in descending order (higher similarity means more similar)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Belirli bir yüzdeden fazlası sıfır olan vektörleri filtreleme
            ZERO_THRESHOLD = 0.3

            filtered_similarities = [
                (patient, similarity) for patient, similarity in similarities
                if zero_percentage(scaled_all_vectors[all_patients.index(patient)]) <= ZERO_THRESHOLD
            ]

            # İlk 5 hastayı al
            similar_patients = [x[0] for x in filtered_similarities[:5]]

            if similar_patients:
                # Prepare data for radar chart
                # Just using the original 5 attributes for the radar chart
                attribute_labels = ['Cinsiyet', 'Yaş', 'Şehir', 'Medeni Durum', 'Eğitim Durumu']
                selected_diagnosis_enum = scaled_all_vectors[selected_index][-1]
                selected_diagnosis = DIAGNOSIS_ENCODING.get(int(selected_diagnosis_enum), "Bilinmiyor")


                selected_data = {
                    'label': f"{selected_patient.isim} {selected_patient.soyisim}",
                    'data': scaled_all_vectors[selected_index][:5]  # Only first 5 attributes for radar
                }

                similar_data = []
                for sp in similar_patients:
                    idx = all_patients.index(sp)
                    similar_data.append({
                        'label': f"{sp.isim} {sp.soyisim}",
                        'data': scaled_all_vectors[idx][:5]
                    })

        except (Hasta.DoesNotExist, ValueError):
            pass

    context = {
        'arama_sonucu': arama_sonucu,
        'selected_patient_id': selected_patient_id,
        'similar_patients': similar_patients,
        'selected_data_json': json.dumps(selected_data),
        'similar_data_json': json.dumps(similar_data),
        'attribute_labels' : attribute_labels
    }

    return render(request, 'patient_similarity.html', context)