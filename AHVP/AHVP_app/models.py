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
        ('adana', 'Adana'), ('ankara', 'Ankara'), ('istanbul', 'İstanbul'),  # Truncated list for brevity
        ('izmir', 'İzmir'), ('antalya', 'Antalya')
    ]

    unique_hasta_id = models.AutoField(primary_key=True)  # Unique patient ID
    isim = models.CharField(max_length=100)
    soyisim = models.CharField(max_length=100)
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_CHOICES)
    yas = models.IntegerField()
    sehir = models.CharField(max_length=100, choices=SEHIR_CHOICES)
    medeni_durum = models.CharField(max_length=100, choices=MEDENI_DURUM_CHOICES)
    egitim_durumu = models.CharField(max_length=100, choices=EGITIM_DURUM_CHOICES)

    def __str__(self):
        return f"{self.isim} {self.soyisim} ({self.unique_hasta_id})"

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
    mmse = models.IntegerField(null=True, blank=True)
    moca = models.IntegerField(null=True, blank=True)
    acer = models.IntegerField(null=True, blank=True)

    # Kan Tahlili Sonuclari
    tam_kan_hb = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_lym = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_neu = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tam_kan_plt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    vitamin_b12 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
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

    # EKG
    ekg_sonucu = models.TextField(null=True, blank=True)

    # EEG
    eeg_sonucu = models.TextField(null=True, blank=True)

    # Ek Testler
    ek_testler = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Muayene {self.id} - Hasta ID: {self.hasta.unique_hasta_id}"

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
