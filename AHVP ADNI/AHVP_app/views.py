from django.shortcuts import render, redirect, get_object_or_404
from .models import Hasta, Muayene, MRISonuc, encrypt
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
from .models import CINSIYET_CHOICES, MEDENI_DURUM_CHOICES

def build_encoding_map(choices):
    return {choice[0]: idx for idx, choice in enumerate(choices)}

CINSIYET_ENCODING = build_encoding_map(CINSIYET_CHOICES)
MEDENI_DURUM_ENCODING = build_encoding_map(MEDENI_DURUM_CHOICES)
DIAGNOSIS_ENCODING = {
    2: 'MCI',
    3: 'Demans',
    5: 'MCI -> Demans'
}

CINSIYET_MAPPING = {
    'Female': 'Kadın',
    'Male': 'Erkek'
}

MEDENI_DURUM_MAPPING = {
    'Married': 'Evli',
    'Widowed': 'Dul',
    'Divorced': 'Boşanmış',
    'Never married': 'Bekar'
}

def patient_to_vector(hasta):
    # Base vector from Hasta
    base_vector = [
        CINSIYET_ENCODING.get(hasta.cinsiyet, -1),
        float(hasta.yas),
        MEDENI_DURUM_ENCODING.get(hasta.medeni_durum, -1),
    ]

    # Get the Muayene with the largest ID
    muayene = Muayene.objects.filter(hasta=hasta).order_by('-id').first()

    if muayene:
        # Cognitive tests (use 0 if None)
        muayene_cognitive = [
            muayene.CDRSB or 0,
            muayene.ADAS11 or 0,
            muayene.ADAS13 or 0,
            muayene.RAVLT_immediate or 0,
            muayene.RAVLT_learning or 0,
            muayene.RAVLT_forgetting or 0,
            muayene.FAQ or 0
        ]

        # FreeSurfer
        freesurfer = MRISonuc.objects.filter(muayene=muayene).first()
        if freesurfer:
            # DecimalField değerlerini al
            freesurfer_fields = [f for f in MRISonuc._meta.get_fields() if isinstance(f, models.DecimalField)]

            # FreeSurfer DecimalField verilerini toplayın
            freesurfer_data = []
            for field in freesurfer_fields:
                value = getattr(freesurfer, field.name, None)
                freesurfer_data.append(float(value or 0))

            # Diagnosis alanını encode edip vektöre ekleyin
            encoded_diagnosis = ""
        else:
            # No FreeSurfer data
            
            freesurfer_fields = [f for f in MRISonuc._meta.get_fields() if isinstance(f, models.DecimalField)]
            freesurfer_data = [0]*len(freesurfer_fields)
    else:
        # No Muayene found:
        muayene_cognitive = [0]*7
        freesurfer_fields = [f for f in MRISonuc._meta.get_fields() if isinstance(f, models.DecimalField)]
        freesurfer_data = [0]*len(freesurfer_fields)

    full_vector = muayene_cognitive +  freesurfer_data
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
        muayene_instance = form.save()
        
        # FreeSurfer dosyasını kontrol et
        mri_freesurfer_file = request.FILES.get('mri_freesurfer')
        if mri_freesurfer_file:
            try:
                # Dosyayı işle ve veritabanına kaydet
                df = pd.read_excel(mri_freesurfer_file)
                mri_data = df.iloc[0]  # İlk satırdaki MRI verileri (örnek)
                MRISonuc.objects.create(
                    muayene=muayene_instance,
                    ventricles=mri_data.get('Ventricles'),
                    hippocampus=mri_data.get('Hippocampus'),
                    whole_brain=mri_data.get('WholeBrain'),
                    entorhinal=mri_data.get('Entorhinal'),
                    fusiform=mri_data.get('Fusiform'),
                    mid_temp=mri_data.get('MidTemp'),
                )
            except Exception as e:
                # Hata mesajı ekleyebilirsiniz
                print(f"Dosya işleme hatası: {e}")
        else:
            # Manual inputları al
            MRISonuc.objects.create(
                muayene=muayene_instance,
                ventricles=request.POST.get('ventricles'),
                hippocampus=request.POST.get('hippocampus'),
                whole_brain=request.POST.get('whole_brain'),
                entorhinal=request.POST.get('entorhinal'),
                fusiform=request.POST.get('fusiform'),
                mid_temp=request.POST.get('mid_temp'),
            )

        return redirect('home')
   
    form = MuayeneForm()
    hasta_list = Hasta.objects.all()
    hasta_options = [(hasta.hasta_id, hasta.hasta_id) for hasta in hasta_list]
    tani_options = [(2, 'MCI'), (3, 'Demans'), (5, 'MCI -> Demans')]

    return render(request, 'new_examination.html', {
        'hasta_options': hasta_options,
        'tani_options': tani_options,
        'form': form
    })

mri_fields = [
    'id',               # MRI sonuçlarının benzersiz kimliği
    'muayene',          # MRI sonuçlarının ilişkili olduğu muayene
    'ventricles',       # Ventrikül hacmi
    'hippocampus',      # Hipokampus hacmi
    'whole_brain',      # Tüm beyin hacmi
    'entorhinal',       # Entorhinal korteks hacmi
    'fusiform',         # Fusiform bölge hacmi
    'mid_temp',         # Orta temporal lob hacmi
]

def get_pretty_attribute_name(attribute_name):
    attribute_mapping = {
        'id': 'Muayene ID',
        'muayene': 'Hasta ID',
        'ventricles': 'Ventricles',
        'hippocampus': 'Hippocampus',
        'whole_brain': 'Whole Brain',
        'entorhinal': 'Entorhinal',
        'fusiform': 'Fusiform',
        'mid_temp': 'Mid Temporal'
    }
    # Eğer attribute_name mapping'de yoksa kendisini döndür
    return attribute_mapping.get(attribute_name, attribute_name)

def create_freesurfer_sonuc(muayene, row):
    return MRISonuc.objects.create(
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

        # Her bir satırı al ve MRISonuc tablosuna ekle
        for _, row in df.iterrows():
            create_freesurfer_sonuc(muayene, row)
                
        print(f"Successfully processed and saved {len(df)} FreeSurfer rows for Muayene {muayene.id}")
        MRISonuc.save()

    except Exception as e:
        print(f"Error processing FreeSurfer file: {e}")

selected_columns = []
def freesurfer_list_view(request):
    global selected_columns
    tanilar = MRISonuc.objects.filter(muayene__tani_encoding__isnull=False).values_list('muayene__tani_encoding', flat=True).distinct()
    
    # Dynamically get all fields from the model
    all_fields = [field.name for field in MRISonuc._meta.get_fields()]

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

    freesurfer_sonuclari = MRISonuc.objects.filter(**filters)
    
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
            field.name for field in MRISonuc._meta.fields 
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
    all_fields = [field.name for field in MRISonuc._meta.get_fields()]

    selected_tani = request.POST.get('tani') or request.GET.get('tani') or 'Tüm Tanılar'
    selected_hasta_id = request.POST.get('hasta_id') or request.GET.get('hasta_id') or ''

    filters = {}
    if selected_tani and selected_tani != 'Tüm Tanılar':
        filters['diagnosis'] = selected_tani
    if selected_hasta_id and selected_hasta_id != '':
        filters['muayene__hasta__hasta_id'] = selected_hasta_id

    freesurfer_sonuclari = MRISonuc.objects.filter(**filters)

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
        all_fields = [field.name for field in MRISonuc._meta.get_fields()]
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
        if 'bulk_visit_submit' in request.POST:
            bulk_file = request.FILES.get('visit_file')
            if not bulk_file:
                return HttpResponse("Belge yüklenmedi.", status=400)

            try:
                df = pd.read_excel(bulk_file)
            except Exception as e:
                return HttpResponse(f"Belgeyi okurken hata: {e}", status=400)
            
            for _, row in df.iterrows():
                # Hasta modelini oluştur veya güncelle
                hasta, created = Hasta.objects.get_or_create(
                    hasta_id=row['RID'],
                    defaults={
                        'cinsiyet': CINSIYET_MAPPING.get(row.get('PTGENDER')) or 'Bilinmiyor',  # İngilizce -> Türkçe çeviri
                        'yas': row['AGE'],
                        'medeni_durum': MEDENI_DURUM_MAPPING.get(row.get('PTMARRY')) or 'Bilinmiyor'  # İngilizce -> Türkçe çeviri
    
                    }
                )

                # Muayene modelini oluştur
                muayene = Muayene.objects.create(
                    hasta=hasta,
                    visit_code=row['VISCODE'],
                    tani_encoding=row['DXCHANGE'],
                    CDRSB=row.get('CDRSB'),
                    ADAS11=row.get('ADAS11'),
                    ADAS13=row.get('ADAS13'),
                    RAVLT_immediate=row.get('RAVLT_immediate'),
                    RAVLT_learning=row.get('RAVLT_learning'),
                    RAVLT_forgetting=row.get('RAVLT_forgetting'),
                    FAQ=row.get('FAQ'),
                )

                # MRI Sonuçlarını oluştur
                MRISonuc.objects.create(
                    muayene=muayene,
                    ventricles=row.get('Ventricles'),
                    hippocampus=row.get('Hippocampus'),
                    whole_brain=row.get('WholeBrain'),
                    entorhinal=row.get('Entorhinal'),
                    fusiform=row.get('Fusiform'),
                    mid_temp=row.get('MidTemp')
                )

            return render(request, 'bulk_data_upload.html', {'message': 'Muayene verisi başarıyla yüklendi.'})
    return render(request, 'bulk_data_upload.html')


def new_patient_view(request):
    if request.method == 'POST':
        # Formdan gelen veriler
        patient_id = request.POST.get('patient_id')  # Hasta ID
        marital_status = request.POST.get('medeni')  # Medeni Durum
        gender = request.POST.get('cinsiyet')       # Cinsiyet
        age = request.POST.get('patient_age')       # Yaş

        # Yeni hasta nesnesi oluşturma
        if patient_id:  # Eğer kullanıcı bir ID girdiyse
            new_patient = Hasta(
                hasta_id=patient_id,
                medeni_durum=marital_status,
                cinsiyet=gender,
                yas=age,
            )
        else:  # Otomatik olarak ID oluştur
            new_patient = Hasta(
                medeni_durum=marital_status,
                cinsiyet=gender,
                yas=age,
            )
        new_patient.save()

        return redirect('home')  # İşlem tamamlandıktan sonra yönlendir

    return render(request, 'new_patient.html', {
        'cinsiyet_options': CINSIYET_CHOICES,
        'medeni_durum_options': MEDENI_DURUM_CHOICES
    })

def search_examination_view(request):
    arama_sonucu = None
    if request.method == "GET":
        arama_kriteri = request.GET.get("arama", "")
        try:
            # Sayısal bir ID girildiyse burada işlenir.
            arama_kriteri_id = int(arama_kriteri)
            arama_sonucu = Muayene.objects.filter(
                Q(hasta_id=arama_kriteri_id) |
                Q(id=arama_kriteri_id)
            )
        except ValueError:
            # Eğer bir isimle arama yapılmak isteniyorsa buradan devam edilir.
            arama_sonucu = []
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

    tanilar = Muayene.objects.values('tani_encoding').annotate(count=Count('tani_encoding')).order_by('tani_encoding')

    # Tanıların adları ve sayıları
    diagnosis_labels = [DIAGNOSIS_ENCODING.get(t['tani_encoding'], 'Bilinmiyor') for t in tanilar]
    diagnosis_counts = [t['count'] for t in tanilar]

    # Count of patients with MRI data
    patients_with_mri = MRISonuc.objects.filter(muayene__hasta__isnull=False).values('muayene__hasta').distinct().count()

    # Count patients without MRI data
    total_patients = Hasta.objects.count()
    patients_without_mri = total_patients - patients_with_mri

    # Her hasta için ziyaret sayısını al
    visit_data = Muayene.objects.values('hasta__hasta_id').annotate(visit_count=Count('id'))

    # Ziyaret sayısı aralıklarını tanımlayın
    visit_bins = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 100)]  # Aralıklar
    visit_labels = [f"{start}-{end}" for start, end in visit_bins]  # Etiketler
    visit_counts = []

    for start, end in visit_bins:
        # Bu aralıktaki hasta sayısını hesapla
        count = sum(1 for item in visit_data if start <= item['visit_count'] <= end)
        visit_counts.append(count)

    return render(request, 'data_report.html', {
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        'age_labels': age_labels,
        'age_counts': age_counts,
        'diagnosis_labels': diagnosis_labels,
        'diagnosis_counts': diagnosis_counts,
        'mri_labels': ['MRI Verisi var', 'MRI Verisi yok'],
        'mri_counts': [patients_with_mri, patients_without_mri],
        'visit_labels': visit_labels,
        'visit_counts': visit_counts,
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
    return generate_csv_response(MRISonuc.objects.all(), "mri.csv")

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
    heatmap_data = []
    attribute_labels = ['Cinsiyet', 'Yaş', 'Medeni Durum', 'CDRSB', 'ADAS11', 'ADAS13', 'RAVLT_immediate', 'RAVLT_learning', 'RAVLT_forgetting', 'FAQ']

    if query:
        # Search patients by name or ID
        arama_sonucu = Hasta.objects.filter(
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
                # Heatmap verisini hazırlayın
                heatmap_data = []
                for patient in [selected_patient] + similar_patients:
                    idx = all_patients.index(patient)
                    heatmap_data.append({
                        'patient_id': patient.hasta_id,
                        'attributes': scaled_all_vectors[idx]
                    })

        except (Hasta.DoesNotExist, ValueError):
            pass

    context = {
        'arama_sonucu': arama_sonucu,
        'selected_patient_id': selected_patient_id,
        'similar_patients': similar_patients,
        'selected_data_json': json.dumps(selected_data),
        'heatmap_data_json': json.dumps(heatmap_data),
        'attribute_labels' : attribute_labels,
        'DIAGNOSIS_ENCODING' : DIAGNOSIS_ENCODING
    }

    return render(request, 'patient_similarity.html', context)