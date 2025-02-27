from django.db import models
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.core.exceptions import ValidationError

class Zone(models.Model):
    ZONE_TYPE_CHOICES = [
        ('master', 'Master'),
        ('slave', 'Slave'),
        ('forward', 'Forward (Cache)'),
        ('redirect', 'Redirect (NoCache)'),
    ]

    name = models.CharField(max_length=255, unique=True, verbose_name="Имя зоны")
    zone_type = models.CharField(max_length=10, choices=ZONE_TYPE_CHOICES, default='master', verbose_name="Тип зоны")
    master_ip = models.CharField(max_length=255, blank=True, null=True, help_text="IP адрес мастера для Slave зоны")
    forwarders = models.CharField(max_length=255, blank=True, null=True, help_text='Для Forward и Redirect')
    ns1 = models.CharField(max_length=255, blank=True, null=True, default='ns1.example.com', verbose_name="NS1")
    ns2 = models.CharField(max_length=255, blank=True, null=True, default='ns2.example.com', verbose_name="NS2")
    ttl = models.IntegerField(blank=True, null=True, default=86400, verbose_name="TTL")
    soa = models.CharField(max_length=255, blank=True, null=True, default='admin.example.com.', verbose_name="SOA")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    serial = models.IntegerField(default=20250123, verbose_name="Serial")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    def __str__(self):
        return self.name

    def clean(self):
        """
        Валидация в зависимости от типа зоны
        """
        if self.zone_type == 'master':
            # Для master обязательны ns1, ns2, ttl, soa
            if not self.ns1 or not self.ns2:
                raise ValidationError("Для master зоны необходимо указать оба NS сервера.")
            if not self.ttl:
                raise ValidationError("Для master зоны необходимо указать TTL.")
            if not self.soa:
                raise ValidationError("Для master зоны необходимо указать SOA.")
        
        elif self.zone_type == 'slave':
            # Для slave обязательны master_ip
            if not self.master_ip:
                raise ValidationError("Для slave зоны необходимо указать master IP.")
            try:
                validate_ipv4_address(self.master_ip)
            except ValidationError:
                raise ValidationError("Некорректный master IP адрес для slave зоны.")
        
        elif self.zone_type in ['forward', 'redirect']:
            # Для forward и redirect обязательны forwarders
            if not self.forwarders:
                raise ValidationError("Необходимо указать forwarders для forward или redirect зоны.")
            # Валидация списка IP-адресов
            forwarder_list = self.forwarders.split(',')
            for ip in forwarder_list:
                try:
                    validate_ipv4_address(ip.strip())
                except ValidationError:
                    raise ValidationError(f"Некорректный IP адрес в forwarders: {ip.strip()}")

    @property
    def is_reverse(self):
        """
        Определяем, является ли зона обратной (reverse).
        """
        return self.name.endswith('.in-addr.arpa') or self.name.endswith('.ip6.arpa')

    @property
    def directory(self):
        """
        Определяем путь хранения в зависимости от типа зоны:
        """
        if self.is_reverse:
            return 'zones/reverse'
        elif self.zone_type == 'slave':
            return 'zones/slave'
        elif self.zone_type in ['forward', 'redirect']:
            return 'zones/forward'
        else:
            return 'zones/master'

    class Meta:
        verbose_name = "Зона"
        verbose_name_plural = "Зоны"


class Record(models.Model):
    RECORD_TYPES = [
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
    ]

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='records')
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)
    name = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, help_text='Значение записи (IP, домен, текст и т.д.)')
    priority = models.IntegerField(blank=True, null=True, help_text='Для MX и SRV записей')
    ttl = models.IntegerField(default=3600)

    def __str__(self):
        return f"{self.name} {self.record_type} {self.value}"

    def clean(self):
        """
        Валидация записей в зависимости от типа:
        """
        if self.record_type == 'A':
            try:
                validate_ipv4_address(self.value)
            except ValidationError:
                raise ValidationError({'value': 'Некорректный IPv4 адрес.'})

        if self.record_type == 'AAAA':
            try:
                validate_ipv6_address(self.value)
            except ValidationError:
                raise ValidationError({'value': 'Некорректный IPv6 адрес.'})

        if self.record_type == 'PTR':
            if not self.value.endswith('.'):
                raise ValidationError({'value': 'PTR запись должна заканчиваться точкой.'})

        if self.record_type in ['MX', 'SRV']:
            if not self.priority:
                raise ValidationError({'priority': 'Для MX и SRV записей необходимо указать priority.'})

    class Meta:
        unique_together = ('zone', 'name', 'record_type', 'value')
        verbose_name = "Запись"
        verbose_name_plural = "Записи"