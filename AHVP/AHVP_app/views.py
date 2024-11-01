from django.shortcuts import render, redirect, get_object_or_404
from .models import Hasta, Muayene, FreeSurferSonuc
from .forms import MuayeneForm
import pandas as pd
from django.db.models import Q
import numpy as np
from django.http import HttpResponse
from django.db import models
from django.contrib import messages
import ast

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
    hasta_options = [(hasta.unique_hasta_id, f"{hasta.isim} {hasta.soyisim}") for hasta in hasta_list]

    return render(request, 'new_examination.html', {
        'hasta_options': hasta_options,
        'form': form
    })

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
    if selected_hasta_id:
        filters['muayene__hasta__unique_hasta_id'] = selected_hasta_id

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
    selected_tani = request.POST.get('tani') or request.GET.get('tani') or 'Tüm Tanılar'

    if selected_tani != 'Tüm Tanılar':
        freesurfer_sonuclari = FreeSurferSonuc.objects.filter(diagnosis=selected_tani)
    else:
        freesurfer_sonuclari = FreeSurferSonuc.objects.all()

    # DataFrame oluşturma
    data = []
    for sonuc in freesurfer_sonuclari:
        data.append({
            'Muayene ID': sonuc.muayene.id,
            'Hasta ID': sonuc.muayene.hasta.unique_hasta_id,
            'Tanı': sonuc.diagnosis,
            'Brain Segmentation Volume': sonuc.brain_seg_vol,
            'Brain Seg Vol Not Vent': sonuc.brain_seg_vol_not_vent,
            'Ventricle Choroid Volume': sonuc.ventricle_choroid_vol,
            'LH Cortex Volume': sonuc.lh_cortex_vol,
            'RH Cortex Volume': sonuc.rh_cortex_vol,
            'Cortex Volume': sonuc.cortex_vol,
            'Left Hemisphere Cerebral White Matter Volume': sonuc.lh_cerebral_white_matter_vol,
            'Right Hemisphere Cerebral White Matter Volume': sonuc.rh_cerebral_white_matter_vol,
            'Cerebral White Matter Volume': sonuc.cerebral_white_matter_vol,
            'Subcortical Gray Matter Volume': sonuc.subcort_gray_vol,
            'Total Gray Matter Volume': sonuc.total_gray_vol,
            'Supra Tentorial Volume': sonuc.supra_tentorial_vol,
            'Supra Tentorial Volume (No Ventricle)': sonuc.supra_tentorial_vol_not_vent,
            'Mask Volume': sonuc.mask_vol,
            'Brain Segmentation Volume to eTIV': sonuc.brain_seg_vol_to_etiv,
            'Mask Volume to eTIV': sonuc.mask_vol_to_etiv,
            'Left Hemisphere Surface Holes': sonuc.lh_surface_holes,
            'Right Hemisphere Surface Holes': sonuc.rh_surface_holes,
            'Surface Holes': sonuc.surface_holes,
            'Estimated Total Intracranial Volume (eTIV)': sonuc.etiv,
            'Left Lateral Ventricle Volume (mm3)': sonuc.left_lateral_ventricle_volume_mm3,
            'Left Lateral Ventricle Norm Mean': sonuc.left_lateral_ventricle_normmean,
            'Left Lateral Ventricle Norm Std Dev': sonuc.left_lateral_ventricle_normstddev,
            'Left Lateral Ventricle Norm Min': sonuc.left_lateral_ventricle_normmin,
            'Left Lateral Ventricle Norm Max': sonuc.left_lateral_ventricle_normmax,
            'Left Lateral Ventricle Norm Range': sonuc.left_lateral_ventricle_normrange,
            'Left Inferior Lateral Ventricle Volume (mm3)': sonuc.left_inf_lat_vent_volume_mm3,
            'Left Inferior Lateral Ventricle Norm Mean': sonuc.left_inf_lat_vent_normmean,
            'Left Inferior Lateral Ventricle Norm Std Dev': sonuc.left_inf_lat_vent_normstddev,
            'Left Inferior Lateral Ventricle Norm Min': sonuc.left_inf_lat_vent_normmin,
            'Left Inferior Lateral Ventricle Norm Max': sonuc.left_inf_lat_vent_normmax,
            'Left Inferior Lateral Ventricle Norm Range': sonuc.left_inf_lat_vent_normrange,
            'Left Cerebellum White Matter Volume (mm3)': sonuc.left_cerebellum_white_matter_volume_mm3,
            'Left Cerebellum White Matter Norm Mean': sonuc.left_cerebellum_white_matter_normmean,
            'Left Cerebellum White Matter Norm Std Dev': sonuc.left_cerebellum_white_matter_normstddev,
            'Left Cerebellum White Matter Norm Min': sonuc.left_cerebellum_white_matter_normmin,
            'Left Cerebellum White Matter Norm Max': sonuc.left_cerebellum_white_matter_normmax,
            'Left Cerebellum White Matter Norm Range': sonuc.left_cerebellum_white_matter_normrange,
            'Left Cerebellum Cortex Volume (mm3)': sonuc.left_cerebellum_cortex_volume_mm3,
            'Left Cerebellum Cortex Norm Mean': sonuc.left_cerebellum_cortex_normmean,
            'Left Cerebellum Cortex Norm Std Dev': sonuc.left_cerebellum_cortex_normstddev,
            'Left Cerebellum Cortex Norm Min': sonuc.left_cerebellum_cortex_normmin,
            'Left Cerebellum Cortex Norm Max': sonuc.left_cerebellum_cortex_normmax,
            'Left Cerebellum Cortex Norm Range': sonuc.left_cerebellum_cortex_normrange,
            'Left Thalamus Volume (mm3)': sonuc.left_thalamus_volume_mm3,
            'Left Thalamus Norm Mean': sonuc.left_thalamus_normmean,
            'Left Thalamus Norm Std Dev': sonuc.left_thalamus_normstddev,
            'Left Thalamus Norm Min': sonuc.left_thalamus_normmin,
            'Left Thalamus Norm Max': sonuc.left_thalamus_normmax,
            'Left Thalamus Norm Range': sonuc.left_thalamus_normrange,
            'Left Caudate Volume (mm3)': sonuc.left_caudate_volume_mm3,
            'Left Caudate Norm Mean': sonuc.left_caudate_normmean,
            'Left Caudate Norm Std Dev': sonuc.left_caudate_normstddev,
            'Left Caudate Norm Min': sonuc.left_caudate_normmin,
            'Left Caudate Norm Max': sonuc.left_caudate_normmax,
            'Left Caudate Norm Range': sonuc.left_caudate_normrange,
            'Left Putamen Volume (mm3)': sonuc.left_putamen_volume_mm3,
            'Left Putamen Norm Mean': sonuc.left_putamen_normmean,
            'Left Putamen Norm Std Dev': sonuc.left_putamen_normstddev,
            'Left Putamen Norm Min': sonuc.left_putamen_normmin,
            'Left Putamen Norm Max': sonuc.left_putamen_normmax,
            'Left Putamen Norm Range': sonuc.left_putamen_normrange,
            'Left Pallidum Volume (mm3)': sonuc.left_pallidum_volume_mm3,
            'Left Pallidum Norm Mean': sonuc.left_pallidum_normmean,
            'Left Pallidum Norm Std Dev': sonuc.left_pallidum_normstddev,
            'Left Pallidum Norm Min': sonuc.left_pallidum_normmin,
            'Left Pallidum Norm Max': sonuc.left_pallidum_normmax,
            'Left Pallidum Norm Range': sonuc.left_pallidum_normrange,
            '3rd Ventricle Volume (mm3)': sonuc.the3rd_ventricle_volume_mm3,
            '3rd Ventricle Norm Mean': sonuc.the3rd_ventricle_normmean,
            '3rd Ventricle Norm Std Dev': sonuc.the3rd_ventricle_normstddev,
            '3rd Ventricle Norm Min': sonuc.the3rd_ventricle_normmin,
            '3rd Ventricle Norm Max': sonuc.the3rd_ventricle_normmax,
            '3rd Ventricle Norm Range': sonuc.the3rd_ventricle_normrange,
            '4th Ventricle Volume (mm3)': sonuc.the4th_ventricle_volume_mm3,
            '4th Ventricle Norm Mean': sonuc.the4th_ventricle_normmean,
            '4th Ventricle Norm Std Dev': sonuc.the4th_ventricle_normstddev,
            '4th Ventricle Norm Min': sonuc.the4th_ventricle_normmin,
            '4th Ventricle Norm Max': sonuc.the4th_ventricle_normmax,
            '4th Ventricle Norm Range': sonuc.the4th_ventricle_normrange,
            'Brain Stem Volume (mm3)': sonuc.brain_stem_volume_mm3,
            'Brain Stem Norm Mean': sonuc.brain_stem_normmean,
            'Brain Stem Norm Std Dev': sonuc.brain_stem_normstddev,
            'Brain Stem Norm Min': sonuc.brain_stem_normmin,
            'Brain Stem Norm Max': sonuc.brain_stem_normmax,
            'Brain Stem Norm Range': sonuc.brain_stem_normrange,
            'Left Hippocampus Volume (mm3)': sonuc.left_hippocampus_volume_mm3,
            'Left Hippocampus Norm Mean': sonuc.left_hippocampus_normmean,
            'Left Hippocampus Norm Std Dev': sonuc.left_hippocampus_normstddev,
            'Left Hippocampus Norm Min': sonuc.left_hippocampus_normmin,
            'Left Hippocampus Norm Max': sonuc.left_hippocampus_normmax,
            'Left Hippocampus Norm Range': sonuc.left_hippocampus_normrange,
            'Left Amygdala Volume (mm3)': sonuc.left_amygdala_volume_mm3,
            'Left Amygdala Norm Mean': sonuc.left_amygdala_normmean,
            'Left Amygdala Norm Std Dev': sonuc.left_amygdala_normstddev,
            'Left Amygdala Norm Min': sonuc.left_amygdala_normmin,
            'Left Amygdala Norm Max': sonuc.left_amygdala_normmax,
            'Left Amygdala Norm Range': sonuc.left_amygdala_normrange,
            'CSF Volume (mm3)': sonuc.csf_volume_mm3,
            'CSF Norm Mean': sonuc.csf_normmean,
            'CSF Norm Std Dev': sonuc.csf_normstddev,
            'CSF Norm Min': sonuc.csf_normmin,
            'CSF Norm Max': sonuc.csf_normmax,
            'CSF Norm Range': sonuc.csf_normrange,
            'Left Accumbens Area Volume (mm3)': sonuc.left_accumbens_area_volume_mm3,
            'Left Accumbens Area Norm Mean': sonuc.left_accumbens_area_normmean,
            'Left Accumbens Area Norm Std Dev': sonuc.left_accumbens_area_normstddev,
            'Left Accumbens Area Norm Min': sonuc.left_accumbens_area_normmin,
            'Left Accumbens Area Norm Max': sonuc.left_accumbens_area_normmax,
            'Left Accumbens Area Norm Range': sonuc.left_accumbens_area_normrange,
            'Left Ventral DC Volume (mm3)': sonuc.left_ventraldc_volume_mm3,
            'Left Ventral DC Norm Mean': sonuc.left_ventraldc_normmean,
            'Left Ventral DC Norm Std Dev': sonuc.left_ventraldc_normstddev,
            'Left Ventral DC Norm Min': sonuc.left_ventraldc_normmin,
            'Left Ventral DC Norm Max': sonuc.left_ventraldc_normmax,
            'Left Ventral DC Norm Range': sonuc.left_ventraldc_normrange,
            'Left Vessel Volume (mm3)': sonuc.left_vessel_volume_mm3,
            'Left Vessel Norm Mean': sonuc.left_vessel_normmean,
            'Left Vessel Norm Std Dev': sonuc.left_vessel_normstddev,
            'Left Vessel Norm Min': sonuc.left_vessel_normmin,
            'Left Vessel Norm Max': sonuc.left_vessel_normmax,
            'Left Vessel Norm Range': sonuc.left_vessel_normrange,
            'Left Choroid Plexus Volume (mm3)': sonuc.left_choroid_plexus_volume_mm3,
            'Left Choroid Plexus Norm Mean': sonuc.left_choroid_plexus_normmean,
            'Left Choroid Plexus Norm Std Dev': sonuc.left_choroid_plexus_normstddev,
            'Left Choroid Plexus Norm Min': sonuc.left_choroid_plexus_normmin,
            'Left Choroid Plexus Norm Max': sonuc.left_choroid_plexus_normmax,
            'Left Choroid Plexus Norm Range': sonuc.left_choroid_plexus_normrange,
            'Right Lateral Ventricle Volume (mm3)': sonuc.right_lateral_ventricle_volume_mm3,
            'Right Lateral Ventricle Norm Mean': sonuc.right_lateral_ventricle_normmean,
            'Right Lateral Ventricle Norm Std Dev': sonuc.right_lateral_ventricle_normstddev,
            'Right Lateral Ventricle Norm Min': sonuc.right_lateral_ventricle_normmin,
            'Right Lateral Ventricle Norm Max': sonuc.right_lateral_ventricle_normmax,
            'Right Lateral Ventricle Norm Range': sonuc.right_lateral_ventricle_normrange,
            'Right Inferior Lateral Ventricle Volume (mm3)': sonuc.right_inf_lat_vent_volume_mm3,
            'Right Inferior Lateral Ventricle Norm Mean': sonuc.right_inf_lat_vent_normmean,
            'Right Inferior Lateral Ventricle Norm Std Dev': sonuc.right_inf_lat_vent_normstddev,
            'Right Inferior Lateral Ventricle Norm Min': sonuc.right_inf_lat_vent_normmin,
            'Right Inferior Lateral Ventricle Norm Max': sonuc.right_inf_lat_vent_normmax,
            'Right Inferior Lateral Ventricle Norm Range': sonuc.right_inf_lat_vent_normrange,
            'Right Cerebellum White Matter Volume (mm3)': sonuc.right_cerebellum_white_matter_volume_mm3,
            'Right Cerebellum White Matter Norm Mean': sonuc.right_cerebellum_white_matter_normmean,
            'Right Cerebellum White Matter Norm Std Dev': sonuc.right_cerebellum_white_matter_normstddev,
            'Right Cerebellum White Matter Norm Min': sonuc.right_cerebellum_white_matter_normmin,
            'Right Cerebellum White Matter Norm Max': sonuc.right_cerebellum_white_matter_normmax,
            'Right Cerebellum White Matter Norm Range': sonuc.right_cerebellum_white_matter_normrange,
            'Right Cerebellum Cortex Volume (mm3)': sonuc.right_cerebellum_cortex_volume_mm3,
            'Right Cerebellum Cortex Norm Mean': sonuc.right_cerebellum_cortex_normmean,
            'Right Cerebellum Cortex Norm Std Dev': sonuc.right_cerebellum_cortex_normstddev,
            'Right Cerebellum Cortex Norm Min': sonuc.right_cerebellum_cortex_normmin,
            'Right Cerebellum Cortex Norm Max': sonuc.right_cerebellum_cortex_normmax,
            'Right Cerebellum Cortex Norm Range': sonuc.right_cerebellum_cortex_normrange,
            'Right Thalamus Volume (mm3)': sonuc.right_thalamus_volume_mm3,
            'Right Thalamus Norm Mean': sonuc.right_thalamus_normmean,
            'Right Thalamus Norm Std Dev': sonuc.right_thalamus_normstddev,
            'Right Thalamus Norm Min': sonuc.right_thalamus_normmin,
            'Right Thalamus Norm Max': sonuc.right_thalamus_normmax,
            'Right Thalamus Norm Range': sonuc.right_thalamus_normrange,
            'Right Caudate Volume (mm3)': sonuc.right_caudate_volume_mm3,
            'Right Caudate Norm Mean': sonuc.right_caudate_normmean,
            'Right Caudate Norm Std Dev': sonuc.right_caudate_normstddev,
            'Right Caudate Norm Min': sonuc.right_caudate_normmin,
            'Right Caudate Norm Max': sonuc.right_caudate_normmax,
            'Right Caudate Norm Range': sonuc.right_caudate_normrange,
            'Right Putamen Volume (mm3)': sonuc.right_putamen_volume_mm3,
            'Right Putamen Norm Mean': sonuc.right_putamen_normmean,
            'Right Putamen Norm Std Dev': sonuc.right_putamen_normstddev,
            'Right Putamen Norm Min': sonuc.right_putamen_normmin,
            'Right Putamen Norm Max': sonuc.right_putamen_normmax,
            'Right Putamen Norm Range': sonuc.right_putamen_normrange,
            'Right Pallidum Volume (mm3)': sonuc.right_pallidum_volume_mm3,
            'Right Pallidum Norm Mean': sonuc.right_pallidum_normmean,
            'Right Pallidum Norm Std Dev': sonuc.right_pallidum_normstddev,
            'Right Pallidum Norm Min': sonuc.right_pallidum_normmin,
            'Right Pallidum Norm Max': sonuc.right_pallidum_normmax,
            'Right Pallidum Norm Range': sonuc.right_pallidum_normrange,
            'Right Hippocampus Volume (mm3)': sonuc.right_hippocampus_volume_mm3,
            'Right Hippocampus Norm Mean': sonuc.right_hippocampus_normmean,
            'Right Hippocampus Norm Std Dev': sonuc.right_hippocampus_normstddev,
            'Right Hippocampus Norm Min': sonuc.right_hippocampus_normmin,
            'Right Hippocampus Norm Max': sonuc.right_hippocampus_normmax,
            'Right Hippocampus Norm Range': sonuc.right_hippocampus_normrange,
            'Right Amygdala Volume (mm3)': sonuc.right_amygdala_volume_mm3,
            'Right Amygdala Norm Mean': sonuc.right_amygdala_normmean,
            'Right Amygdala Norm Std Dev': sonuc.right_amygdala_normstddev,
            'Right Amygdala Norm Min': sonuc.right_amygdala_normmin,
            'Right Amygdala Norm Max': sonuc.right_amygdala_normmax,
            'Right Amygdala Norm Range': sonuc.right_amygdala_normrange,
            'Right Accumbens Area Volume (mm3)': sonuc.right_accumbens_area_volume_mm3,
            'Right Accumbens Area Norm Mean': sonuc.right_accumbens_area_normmean,
            'Right Accumbens Area Norm Std Dev': sonuc.right_accumbens_area_normstddev,
            'Right Accumbens Area Norm Min': sonuc.right_accumbens_area_normmin,
            'Right Accumbens Area Norm Max': sonuc.right_accumbens_area_normmax,
            'Right Accumbens Area Norm Range': sonuc.right_accumbens_area_normrange,
            'Right Ventral DC Volume (mm3)': sonuc.right_ventraldc_volume_mm3,
            'Right Ventral DC Norm Mean': sonuc.right_ventraldc_normmean,
            'Right Ventral DC Norm Std Dev': sonuc.right_ventraldc_normstddev,
            'Right Ventral DC Norm Min': sonuc.right_ventraldc_normmin,
            'Right Ventral DC Norm Max': sonuc.right_ventraldc_normmax,
            'Right Ventral DC Norm Range': sonuc.right_ventraldc_normrange,
            'Right Vessel Volume (mm3)': sonuc.right_vessel_volume_mm3,
            'Right Vessel Norm Mean': sonuc.right_vessel_normmean,
            'Right Vessel Norm Std Dev': sonuc.right_vessel_normstddev,
            'Right Vessel Norm Min': sonuc.right_vessel_normmin,
            'Right Vessel Norm Max': sonuc.right_vessel_normmax,
            'Right Vessel Norm Range': sonuc.right_vessel_normrange,
            'Right Choroid Plexus Volume (mm3)': sonuc.right_choroid_plexus_volume_mm3,
            'Right Choroid Plexus Norm Mean': sonuc.right_choroid_plexus_normmean,
            'Right Choroid Plexus Norm Std Dev': sonuc.right_choroid_plexus_normstddev,
            'Right Choroid Plexus Norm Min': sonuc.right_choroid_plexus_normmin,
            'Right Choroid Plexus Norm Max': sonuc.right_choroid_plexus_normmax,
            'Right Choroid Plexus Norm Range': sonuc.right_choroid_plexus_normrange,
            '5th Ventricle Volume (mm3)': sonuc.the5th_ventricle_volume_mm3,
            '5th Ventricle Norm Mean': sonuc.the5th_ventricle_normmean,
            '5th Ventricle Norm Std Dev': sonuc.the5th_ventricle_normstddev,
            '5th Ventricle Norm Min': sonuc.the5th_ventricle_normmin,
            '5th Ventricle Norm Max': sonuc.the5th_ventricle_normmax,
            '5th Ventricle Norm Range': sonuc.the5th_ventricle_normrange,
            'WM Hypointensities Volume (mm3)': sonuc.wm_hypointensities_volume_mm3,
            'WM Hypointensities Norm Mean': sonuc.wm_hypointensities_normmean,
            'WM Hypointensities Norm Std Dev': sonuc.wm_hypointensities_normstddev,
            'WM Hypointensities Norm Min': sonuc.wm_hypointensities_normmin,
            'WM Hypointensities Norm Max': sonuc.wm_hypointensities_normmax,
            'WM Hypointensities Norm Range': sonuc.wm_hypointensities_normrange,
            'Left WM Hypointensities Volume (mm3)': sonuc.left_wm_hypointensities_volume_mm3,
            'Left WM Hypointensities Norm Mean': sonuc.left_wm_hypointensities_normmean,
            'Left WM Hypointensities Norm Std Dev': sonuc.left_wm_hypointensities_normstddev,
            'Left WM Hypointensities Norm Min': sonuc.left_wm_hypointensities_normmin,
            'Left WM Hypointensities Norm Max': sonuc.left_wm_hypointensities_normmax,
            'Left WM Hypointensities Norm Range': sonuc.left_wm_hypointensities_normrange,
            'Right WM Hypointensities Volume (mm3)': sonuc.right_wm_hypointensities_volume_mm3,
            'Right WM Hypointensities Norm Mean': sonuc.right_wm_hypointensities_normmean,
            'Right WM Hypointensities Norm Std Dev': sonuc.right_wm_hypointensities_normstddev,
            'Right WM Hypointensities Norm Min': sonuc.right_wm_hypointensities_normmin,
            'Right WM Hypointensities Norm Max': sonuc.right_wm_hypointensities_normmax,
            'Right WM Hypointensities Norm Range': sonuc.right_wm_hypointensities_normrange,
            'Non-WM Hypointensities Volume (mm3)': sonuc.non_wm_hypointensities_volume_mm3,
            'Non-WM Hypointensities Norm Mean': sonuc.non_wm_hypointensities_normmean,
            'Non-WM Hypointensities Norm Std Dev': sonuc.non_wm_hypointensities_normstddev,
            'Non-WM Hypointensities Norm Min': sonuc.non_wm_hypointensities_normmin,
            'Non-WM Hypointensities Norm Max': sonuc.non_wm_hypointensities_normmax,
            'Non-WM Hypointensities Norm Range': sonuc.non_wm_hypointensities_normrange,
            'Left Non-WM Hypointensities Volume (mm3)': sonuc.left_non_wm_hypointensities_volume_mm3,
            'Left Non-WM Hypointensities Norm Mean': sonuc.left_non_wm_hypointensities_normmean,
            'Left Non-WM Hypointensities Norm Std Dev': sonuc.left_non_wm_hypointensities_normstddev,
            'Left Non-WM Hypointensities Norm Min': sonuc.left_non_wm_hypointensities_normmin,
            'Left Non-WM Hypointensities Norm Max': sonuc.left_non_wm_hypointensities_normmax,
            'Left Non-WM Hypointensities Norm Range': sonuc.left_non_wm_hypointensities_normrange,
            'Right Non-WM Hypointensities Volume (mm3)': sonuc.right_non_wm_hypointensities_volume_mm3,
            'Right Non-WM Hypointensities Norm Mean': sonuc.right_non_wm_hypointensities_normmean,
            'Right Non-WM Hypointensities Norm Std Dev': sonuc.right_non_wm_hypointensities_normstddev,
            'Right Non-WM Hypointensities Norm Min': sonuc.right_non_wm_hypointensities_normmin,
            'Right Non-WM Hypointensities Norm Max': sonuc.right_non_wm_hypointensities_normmax,
            'Right Non-WM Hypointensities Norm Range': sonuc.right_non_wm_hypointensities_normrange,
            'Optic Chiasm Volume (mm3)': sonuc.optic_chiasm_volume_mm3,
            'Optic Chiasm Norm Mean': sonuc.optic_chiasm_normmean,
            'Optic Chiasm Norm Std Dev': sonuc.optic_chiasm_normstddev,
            'Optic Chiasm Norm Min': sonuc.optic_chiasm_normmin,
            'Optic Chiasm Norm Max': sonuc.optic_chiasm_normmax,
            'Optic Chiasm Norm Range': sonuc.optic_chiasm_normrange,
            'CC Posterior Volume (mm3)': sonuc.cc_posterior_volume_mm3,
            'CC Posterior Norm Mean': sonuc.cc_posterior_normmean,
            'CC Posterior Norm Std Dev': sonuc.cc_posterior_normstddev,
            'CC Posterior Norm Min': sonuc.cc_posterior_normmin,
            'CC Posterior Norm Max': sonuc.cc_posterior_normmax,
            'CC Posterior Norm Range': sonuc.cc_posterior_normrange,
            'CC Mid Posterior Volume (mm3)': sonuc.cc_mid_posterior_volume_mm3,
            'CC Mid Posterior Norm Mean': sonuc.cc_mid_posterior_normmean,
            'CC Mid Posterior Norm Std Dev': sonuc.cc_mid_posterior_normstddev,
            'CC Mid Posterior Norm Min': sonuc.cc_mid_posterior_normmin,
            'CC Mid Posterior Norm Max': sonuc.cc_mid_posterior_normmax,
            'CC Mid Posterior Norm Range': sonuc.cc_mid_posterior_normrange,
            'CC Central Volume (mm3)': sonuc.cc_central_volume_mm3,
            'CC Central Norm Mean': sonuc.cc_central_normmean,
            'CC Central Norm Std Dev': sonuc.cc_central_normstddev,
            'CC Central Norm Min': sonuc.cc_central_normmin,
            'CC Central Norm Max': sonuc.cc_central_normmax,
            'CC Central Norm Range': sonuc.cc_central_normrange,
            'CC Mid Anterior Volume (mm3)': sonuc.cc_mid_anterior_volume_mm3,
            'CC Mid Anterior Norm Mean': sonuc.cc_mid_anterior_normmean,
            'CC Mid Anterior Norm Std Dev': sonuc.cc_mid_anterior_normstddev,
            'CC Mid Anterior Norm Min': sonuc.cc_mid_anterior_normmin,
            'CC Mid Anterior Norm Max': sonuc.cc_mid_anterior_normmax,
            'CC Mid Anterior Norm Range': sonuc.cc_mid_anterior_normrange,
            'CC Anterior Volume (mm3)': sonuc.cc_anterior_volume_mm3,
            'CC Anterior Norm Mean': sonuc.cc_anterior_normmean,
            'CC Anterior Norm Std Dev': sonuc.cc_anterior_normstddev,
            'CC Anterior Norm Min': sonuc.cc_anterior_normmin,
            'CC Anterior Norm Max': sonuc.cc_anterior_normmax,
            'CC Anterior Norm Range': sonuc.cc_anterior_normrange
        })

    df = pd.DataFrame(data)

    # Excel dosyasına yazdır
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="freesurfer_sonuclari.xlsx"'
    df.to_excel(response, index=False)

    return response

def upload_bulk_mri_results_view(request):
    if request.method == 'POST':
        mri_file = request.FILES.get('bulk_mri_file')
        if not mri_file:
            return HttpResponse("No file uploaded", status=400)

        try:
            df = pd.read_excel(mri_file)
        except Exception as e:
            return HttpResponse(f"Error reading file: {e}", status=400)

        for _, row in df.iterrows():
            hasta_id = row.get('Patient_ID')
            try:
                hasta = Hasta.objects.get(unique_hasta_id=hasta_id)
            except Hasta.DoesNotExist:
                print(f"Hasta ID {hasta_id} bulunamadı, atlanıyor.")
                continue  
            muayene = Muayene.objects.create(hasta=hasta)

            create_freesurfer_sonuc(muayene, row)

        return render(request, 'bulk_data_upload.html')
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