from django.db import models

class Zone(models.Model):
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=10, choices=[
        ('forward', 'Forward'),
        ('reverse', 'Reverse')
    ])
    ttl = models.IntegerField(default=3600)

    def __str__(self):
        return self.name


class Record(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='records')
    type = models.CharField(max_length=10, choices=[
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('CNAME', 'CNAME'),
        ('MX', 'MX'),
        ('TXT', 'TXT'),
        ('NS', 'NS'),
        ('PTR', 'PTR'),
        ('SRV', 'SRV'),
        ('CAA', 'CAA'),
        ('SOA', 'SOA'),
    ])
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255)
    priority = models.IntegerField(blank=True, null=True)  # Для MX и SRV
    ttl = models.IntegerField(default=3600)

    def __str__(self):
        return f"{self.name} {self.type} {self.value}"