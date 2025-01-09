from django.db import models
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime

# AES encryption key (store securely in real projects)
KEY = b'rIPBI43WwbPzTGoUmrkF7mENYpIMYXkXorviVCj31LY='
cipher_suite = Fernet(KEY)

CINSIYET_CHOICES = [('kadın', 'Kadın'), ('erkek', 'Erkek')]
MEDENI_DURUM_CHOICES = [('evli', 'Evli'), ('bekar', 'Bekar'), ('boşanmış', 'Boşanmış')]

# Encryption function
def encrypt(data):
    return cipher_suite.encrypt(data.encode())

# Decryption function
def decrypt(data):
    return cipher_suite.decrypt(data).decode()

class Hasta(models.Model):
    hasta_id = models.IntegerField(primary_key=True)
    cinsiyet = models.CharField(max_length=10, choices=CINSIYET_CHOICES)
    yas = models.FloatField()
    medeni_durum = models.CharField(max_length=100, choices=MEDENI_DURUM_CHOICES)

    def save(self, *args, **kwargs):
        if not self.hasta_id:  # ID sağlanmamışsa otomatik bir değer oluştur
            max_id = Hasta.objects.aggregate(max_id=models.Max('hasta_id'))['max_id']
            self.hasta_id = max(max_id + 1 if max_id else 5300, 5300)  # En az 5300 ile başlar!!
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hasta_id}"

class Muayene(models.Model):
    hasta = models.ForeignKey(Hasta, on_delete=models.CASCADE)  # The examination belongs to a patient
    sifrelenmis_tarih = models.CharField(max_length=255)  # Encrypted date
    visit_code = models.CharField(max_length=255, null=True, blank=True)  # Visit code
    tani_encoding = models.IntegerField(null=True, blank=True)

    CDRSB = models.FloatField(null=True, blank=True)
    ADAS11 = models.FloatField(null=True, blank=True)
    ADAS13 = models.FloatField(null=True, blank=True)
    RAVLT_immediate = models.FloatField(null=True, blank=True)
    RAVLT_learning = models.FloatField(null=True, blank=True)
    RAVLT_forgetting = models.FloatField(null=True, blank=True)
    FAQ = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}" 
    
    # Save method to automatically encrypt the date
    def save(self, *args, **kwargs):
        if not self.sifrelenmis_tarih:  # Encrypt only if it's not already set
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current time
            self.sifrelenmis_tarih = encrypt(now)  # Encrypt the current time
        super().save(*args, **kwargs)

    def get_decrypted_date(self):
        # Tarihi güvenli bir şekilde çöz
        try:
            return cipher_suite.decrypt(self.sifrelenmis_tarih.encode()).decode()
        except InvalidToken:
            return "Geçersiz şifrelenmiş veri"

    @staticmethod
    def calculate_time_between_visits(visit1, visit2):
        try:
            # İlk muayene tarihini çöz
            date1 = datetime.strptime(
                cipher_suite.decrypt(visit1.sifrelenmis_tarih.encode()).decode(), 
                '%Y-%m-%d %H:%M:%S'
            )
            # İkinci muayene tarihini çöz
            date2 = datetime.strptime(
                cipher_suite.decrypt(visit2.sifrelenmis_tarih.encode()).decode(), 
                '%Y-%m-%d %H:%M:%S'
            )
            # İki tarih arasındaki farkı döndür
            return abs(date2 - date1)  # timedelta
        except InvalidToken:
            return "Şifre çözme hatası: Geçersiz token"

class MRISonuc(models.Model):
    muayene = models.ForeignKey(Muayene, on_delete=models.CASCADE)  # FreeSurfer sonuçları muayene ile ilişkili
    ventricles = models.FloatField(null=True, blank=True)
    hippocampus = models.FloatField(null=True, blank=True)
    whole_brain = models.FloatField(null=True, blank=True)
    entorhinal = models.FloatField(null=True, blank=True)
    fusiform = models.FloatField(null=True, blank=True)
    mid_temp = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"FreeSurfer Result for Muayene ID: {self.muayene.id}"
