from django.db import models
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

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
    CINSIYET_CHOICES = [
        ('kadın', 'Kadın'),
        ('erkek', 'Erkek')
    ]

    MEDENI_DURUM_CHOICES = [
        ('evli', 'Evli'),
        ('bekar', 'Bekar'),
        ('boşanmış', 'Boşanmış')
    ]

    EGITIM_DURUM_CHOICES = [
        ('lise', 'Lise'),
        ('lisans', 'Lisans'),
        ('yok', 'Yok')
    ]

    SEHIR_CHOICES = [
        ('adana', 'Adana'), ('adiyaman', 'Adıyaman'), ('afyonkarahisar', 'Afyonkarahisar'),
        ('agri', 'Ağrı'), ('amasya', 'Amasya'), ('ankara', 'Ankara'), 
        ('antalya', 'Antalya'), ('artvin', 'Artvin'), ('aydin', 'Aydın'),
        ('balikesir', 'Balıkesir'), ('batman', 'Batman'), ('bayburt', 'Bayburt'),
        ('bilecik', 'Bilecik'), ('bingol', 'Bingöl'), ('bitlis', 'Bitlis'),
        ('bolu', 'Bolu'), ('burdur', 'Burdur'), ('bursa', 'Bursa'),
        ('canakkale', 'Çanakkale'), ('cankiri', 'Çankırı'), ('corum', 'Çorum'),
        ('denizli', 'Denizli'), ('diyarbakir', 'Diyarbakır'), ('edirne', 'Edirne'),
        ('elazig', 'Elazığ'), ('erzincan', 'Erzincan'), ('erzurum', 'Erzurum'),
        ('eskisehir', 'Eskişehir'), ('gaziantep', 'Gaziantep'), ('giresun', 'Giresun'),
        ('gumushane', 'Gümüşhane'), ('hakkari', 'Hakkari'), ('hatay', 'Hatay'),
        ('igdir', 'Iğdır'), ('istanbul', 'İstanbul'), ('izmir', 'İzmir'),
        ('karabuk', 'Karabük'), ('karaman', 'Karaman'), ('kars', 'Kars'),
        ('kastamonu', 'Kastamonu'), ('kayseri', 'Kayseri'), ('kilis', 'Kilis'),
        ('kirikkale', 'Kırıkkale'), ('kirsehir', 'Kırşehir'), ('konya', 'Konya'),
        ('kutahya', 'Kütahya'), ('malatya', 'Malatya'), ('manisa', 'Manisa'),
        ('mardin', 'Mardin'), ('mersin', 'Mersin'), ('muğla', 'Muğla'),
        ('nevsehir', 'Nevşehir'), ('nigde', 'Niğde'), ('ordu', 'Ordu'),
        ('osmaniye', 'Osmaniye'), ('rize', 'Rize'), ('sakarya', 'Sakarya'),
        ('samsun', 'Samsun'), ('sanliurfa', 'Şanlıurfa'), ('siirt', 'Siirt'),
        ('sinop', 'Sinop'), ('sivas', 'Sivas'), ('tekirdag', 'Tekirdağ'),
        ('tokat', 'Tokat'), ('trabzon', 'Trabzon'), ('tunceli', 'Tunceli'),
        ('usak', 'Uşak'), ('van', 'Van'), ('yalova', 'Yalova'),
        ('yozgat', 'Yozgat'), ('zonguldak', 'Zonguldak')
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
