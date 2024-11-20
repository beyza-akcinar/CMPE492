from django.db import models
from cryptography.fernet import Fernet
from datetime import datetime

# AES encryption key (store securely in real projects)
KEY = Fernet.generate_key()
cipher_suite = Fernet(KEY)

# Encryption function
def encrypt(data):
    return cipher_suite.encrypt(data.encode())

# Decryption function
def decrypt(data):
    return cipher_suite.decrypt(data).decode()

class Hasta(models.Model):
    CINSIYET_CHOICES = [('kadın', 'Kadın'), ('erkek', 'Erkek')]
    MEDENI_DURUM_CHOICES = [('evli', 'Evli'), ('bekar', 'Bekar'), ('boşanmış', 'Boşanmış')]
    EGITIM_DURUM_CHOICES = [('lise', 'Lise'), ('lisans', 'Lisans'), ('yok', 'Yok')]
    SEHIR_CHOICES = [
        ('adana', 'Adana'),
        ('adiyaman', 'Adıyaman'),
        ('afyonkarahisar', 'Afyonkarahisar'),
        ('agri', 'Ağrı'),
        ('amasya', 'Amasya'),
        ('ankara', 'Ankara'),
        ('antalya', 'Antalya'),
        ('artvin', 'Artvin'),
        ('aydin', 'Aydın'),
        ('balikesir', 'Balıkesir'),
        ('batman', 'Batman'),
        ('bayburt', 'Bayburt'),
        ('bilecik', 'Bilecik'),
        ('bingol', 'Bingöl'),
        ('bitlis', 'Bitlis'),
        ('bolu', 'Bolu'),
        ('burdur', 'Burdur'),
        ('burgaz', 'Burgaz'),
        ('canakkale', 'Çanakkale'),
        ('cankiri', 'Çankırı'),
        ('corum', 'Çorum'),
        ('denizli', 'Denizli'),
        ('diyarbakir', 'Diyarbakır'),
        ('edirne', 'Edirne'),
        ('elazig', 'Elazığ'),
        ('erzincan', 'Erzincan'),
        ('erzurum', 'Erzurum'),
        ('eskisehir', 'Eskişehir'),
        ('gaziantep', 'Gaziantep'),
        ('giresun', 'Giresun'),
        ('gumushane', 'Gümüşhane'),
        ('hakkari', 'Hakkari'),
        ('hatay', 'Hatay'),
        ('igdir', 'Iğdır'),
        ('izmir', 'İzmir'),
        ('karabuk', 'Karabük'),
        ('karaman', 'Karaman'),
        ('kastamonu', 'Kastamonu'),
        ('kayseri', 'Kayseri'),
        ('kirikkale', 'Kırıkkale'),
        ('kirsehir', 'Kırşehir'),
        ('kilis', 'Kilis'),
        ('konya', 'Konya'),
        ('kutahya', 'Kütahya'),
        ('malatya', 'Malatya'),
        ('manisa', 'Manisa'),
        ('mardin', 'Mardin'),
        ('mugla', 'Muğla'),
        ('mus', 'Muş'),
        ('nevsehir', 'Nevşehir'),
        ('nigde', 'Niğde'),
        ('ordu', 'Ordu'),
        ('rize', 'Rize'),
        ('sakarya', 'Sakarya'),
        ('samsun', 'Samsun'),
        ('siirt', 'Siirt'),
        ('sinop', 'Sinop'),
        ('sivas', 'Sivas'),
        ('tekirdag', 'Tekirdağ'),
        ('tokat', 'Tokat'),
        ('trabzon', 'Trabzon'),
        ('tunceli', 'Tunceli'),
        ('ustkoy', 'Uşak'),
        ('van', 'Van'),
        ('yalova', 'Yalova'),
        ('yozgat', 'Yozgat'),
        ('zonguldak', 'Zonguldak'),
    ]

    hasta_id = models.AutoField(primary_key=True) 
    isim = models.CharField(max_length=100)
    soyisim = models.CharField(max_length=100)
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_CHOICES)
    yas = models.IntegerField()
    sehir = models.CharField(max_length=100, choices=SEHIR_CHOICES)
    medeni_durum = models.CharField(max_length=100, choices=MEDENI_DURUM_CHOICES)
    egitim_durumu = models.CharField(max_length=100, choices=EGITIM_DURUM_CHOICES)
    meslek = models.CharField(max_length=100)


    def __str__(self):
        return f"{self.hasta_id}"

class Muayene(models.Model):
    hasta = models.ForeignKey(Hasta, on_delete=models.CASCADE)  # The examination belongs to a patient
    sifrelenmis_tarih = models.CharField(max_length=255)  # Encrypted date

    # Patolojik Bulgular
    denge_bozuklugu = models.BooleanField(default=False)
    serebellar_bulgular = models.BooleanField(default=False)
    ense_sertligi = models.BooleanField(default=False)
    parkinsonizm = models.BooleanField(default=False)
    kranial_sinir_bulgulari = models.BooleanField(default=False)
    motor_duygusal_bulgular = models.BooleanField(default=False)
    patolojik_refleks = models.BooleanField(default=False)

    # Bilissel Test Sonuclari
    acer = models.IntegerField(null=True, blank=True)
    npt = models.IntegerField(null=True, blank=True)
    beck_depresyon = models.IntegerField(null=True, blank=True)
    beck_anksiyete = models.IntegerField(null=True, blank=True)
    geriatrik_depresyon = models.IntegerField(null=True, blank=True)
    mmse_zaman = models.IntegerField(null=True, blank=True)
    mmse_yer = models.IntegerField(null=True, blank=True)
    mmse_kayithafizasi = models.IntegerField(null=True, blank=True)
    mmse_dikkat = models.IntegerField(null=True, blank=True)
    mmse_hatirlama = models.IntegerField(null=True, blank=True)
    mmse_lisan = models.IntegerField(null=True, blank=True)
    mmse = models.IntegerField(null=True, blank=True)

    # Kan Tahlili Sonuclari
    glukoz = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_hb = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_lym = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_neu = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_plt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vitamin_b12 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tiroid_fonksiyon = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ast = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    alt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ldh = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bun = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    kreatinin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    uric_acid = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    eritrosit = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sedim = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vldrl = models.CharField(max_length=100, null=True, blank=True)

    # BT
    bt_sonucu = models.TextField(null=True, blank=True)

    # MRI
    mri_notlari = models.TextField(null=True, blank=True)
    mri_tarihi = models.DateField(null=True, blank=True)
    mri_freesurfer = models.FileField(upload_to='mri/', null=True, blank=True)

    # PET
    pet1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet5 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet6 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet7 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet8 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet9 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pet10 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # PA Akciğer Grafisi
    pa_akciger_grafisi = models.TextField(null=True, blank=True)

    # EEG
    eeg_sonucu = models.TextField(null=True, blank=True)
    eeg_file = models.FileField(upload_to='mri/', null=True, blank=True)

    #BOS
    amiloid = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tau = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Ek Testler
    ek_testler = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}" 
    
    # Save method to automatically encrypt the date
    def save(self, *args, **kwargs):
        if not self.sifrelenmis_tarih:  # Encrypt only if it's not already set
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current time
            self.sifrelenmis_tarih = encrypt(now)  # Encrypt the current time
        super().save(*args, **kwargs)

    # Method to decrypt the date
    def get_decrypted_date(self):
        return decrypt(self.sifrelenmis_tarih)

    # Static method to calculate time difference between two visits
    @staticmethod
    def calculate_time_between_visits(visit1, visit2):
        date1 = datetime.strptime(decrypt(visit1.sifrelenmis_tarih), '%Y-%m-%d %H:%M:%S')
        date2 = datetime.strptime(decrypt(visit2.sifrelenmis_tarih), '%Y-%m-%d %H:%M:%S')
        return abs(date2 - date1)  # Return the difference as a timedelta object

class FreeSurferSonuc(models.Model):
    muayene = models.ForeignKey(Muayene, on_delete=models.CASCADE)  # FreeSurfer sonuçları muayene ile ilişkili
    diagnosis = models.CharField(max_length=255)
    brain_seg_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_seg_vol_not_vent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ventricle_choroid_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lh_cortex_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rh_cortex_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cortex_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lh_cerebral_white_matter_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rh_cerebral_white_matter_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cerebral_white_matter_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subcort_gray_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_gray_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supra_tentorial_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supra_tentorial_vol_not_vent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mask_vol = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_seg_vol_to_etiv = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    mask_vol_to_etiv = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    lh_surface_holes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rh_surface_holes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    surface_holes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    etiv = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_lateral_ventricle_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_inf_lat_vent_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_inf_lat_vent_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_inf_lat_vent_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_inf_lat_vent_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_inf_lat_vent_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_inf_lat_vent_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_cerebellum_white_matter_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_white_matter_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_white_matter_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_white_matter_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_white_matter_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_white_matter_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_cerebellum_cortex_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_cortex_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_cortex_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_cortex_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_cortex_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_cerebellum_cortex_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_thalamus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_thalamus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_thalamus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_thalamus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_thalamus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_thalamus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    left_caudate_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_caudate_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_caudate_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_caudate_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_caudate_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_caudate_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_putamen_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_putamen_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_putamen_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_putamen_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_putamen_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_putamen_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_pallidum_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_pallidum_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_pallidum_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_pallidum_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_pallidum_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_pallidum_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    the3rd_ventricle_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the3rd_ventricle_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the3rd_ventricle_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the3rd_ventricle_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the3rd_ventricle_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the3rd_ventricle_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    the4th_ventricle_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the4th_ventricle_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the4th_ventricle_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the4th_ventricle_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the4th_ventricle_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the4th_ventricle_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    brain_stem_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_stem_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_stem_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_stem_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_stem_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brain_stem_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_hippocampus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_hippocampus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_hippocampus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_hippocampus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_hippocampus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_hippocampus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_amygdala_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_amygdala_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_amygdala_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_amygdala_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_amygdala_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_amygdala_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    csf_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    csf_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    csf_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    csf_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    csf_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    csf_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_accumbens_area_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_accumbens_area_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_accumbens_area_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_accumbens_area_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_accumbens_area_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_accumbens_area_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_ventraldc_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_ventraldc_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_ventraldc_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_ventraldc_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_ventraldc_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_ventraldc_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_vessel_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_vessel_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_vessel_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_vessel_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_vessel_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_vessel_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_choroid_plexus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_choroid_plexus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_choroid_plexus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_choroid_plexus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_choroid_plexus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_choroid_plexus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_lateral_ventricle_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_lateral_ventricle_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_lateral_ventricle_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_lateral_ventricle_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_lateral_ventricle_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_lateral_ventricle_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_inf_lat_vent_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_inf_lat_vent_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_inf_lat_vent_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_inf_lat_vent_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_inf_lat_vent_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_inf_lat_vent_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_cerebellum_white_matter_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_white_matter_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_white_matter_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_white_matter_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_white_matter_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_white_matter_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_cerebellum_cortex_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_cortex_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_cortex_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_cortex_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_cortex_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_cerebellum_cortex_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_thalamus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_thalamus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_thalamus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_thalamus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_thalamus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_thalamus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_caudate_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_caudate_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_caudate_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_caudate_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_caudate_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_caudate_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_putamen_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_putamen_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_putamen_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_putamen_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_putamen_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_putamen_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_pallidum_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_pallidum_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_pallidum_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_pallidum_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_pallidum_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_pallidum_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_hippocampus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_hippocampus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_hippocampus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_hippocampus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_hippocampus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_hippocampus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_amygdala_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_amygdala_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_amygdala_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_amygdala_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_amygdala_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_amygdala_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_accumbens_area_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_accumbens_area_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_accumbens_area_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_accumbens_area_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_accumbens_area_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_accumbens_area_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_ventraldc_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_ventraldc_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_ventraldc_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_ventraldc_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_ventraldc_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_ventraldc_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_vessel_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_vessel_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_vessel_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_vessel_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_vessel_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_vessel_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_choroid_plexus_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_choroid_plexus_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_choroid_plexus_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_choroid_plexus_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_choroid_plexus_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_choroid_plexus_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    the5th_ventricle_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the5th_ventricle_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the5th_ventricle_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the5th_ventricle_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the5th_ventricle_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    the5th_ventricle_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    non_wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    non_wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    non_wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    non_wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    non_wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    non_wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    left_non_wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_non_wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_non_wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_non_wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_non_wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    left_non_wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    right_non_wm_hypointensities_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_non_wm_hypointensities_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_non_wm_hypointensities_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_non_wm_hypointensities_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_non_wm_hypointensities_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    right_non_wm_hypointensities_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    optic_chiasm_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optic_chiasm_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optic_chiasm_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optic_chiasm_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optic_chiasm_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    optic_chiasm_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cc_posterior_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_posterior_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_posterior_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_posterior_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_posterior_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_posterior_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cc_mid_posterior_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_posterior_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_posterior_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_posterior_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_posterior_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_posterior_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cc_central_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_central_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_central_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_central_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_central_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_central_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cc_mid_anterior_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_anterior_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_anterior_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_anterior_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_anterior_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_mid_anterior_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    cc_anterior_volume_mm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_anterior_normmean = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_anterior_normstddev = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_anterior_normmin = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_anterior_normmax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cc_anterior_normrange = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)



    def __str__(self):
        return f"FreeSurfer Result for Muayene ID: {self.muayene.id}"
