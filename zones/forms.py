from django import forms
from .models import Zone
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError

class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'zone_type', 'master_ip', 'forwarders', 'ns1', 'ns2', 'ttl', 'soa', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'nlgate.local',
                'autocomplete': 'off'
            }),
            'zone_type': forms.Select(attrs={
                'class': 'select'
            }),
            'master_ip': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'IP адрес мастера (только для Slave зон)'
            }),
            'forwarders': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'IP-адреса через запятую (например: 8.8.8.8, 8.8.4.4)'
            }),
            'ns1': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'ns1.nlgate.local'
            }),
            'ns2': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'ns2.nlgate.local'
            }),
            'ttl': forms.NumberInput(attrs={
                'class': 'input', 
                'placeholder': '86400'
            }),
            'soa': forms.TextInput(attrs={
                'class': 'input', 
                'placeholder': 'admin.nlgate.local.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 
                'placeholder': 'Описание зоны (опционально)'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Zone.objects.filter(name=name).exists():
            raise ValidationError(f"Зона с именем '{name}' уже существует.")
        return name

    def clean_master_ip(self):
        """
        Проверяем правильность введённого IP-адреса для master_ip.
        """
        master_ip = self.cleaned_data.get('master_ip')
        if master_ip:
            try:
                validate_ipv4_address(master_ip)
            except ValidationError:
                raise ValidationError("Некорректный IP-адрес мастера.")
        return master_ip

    def clean(self):
        """
        Очищаем поля в зависимости от выбранного типа зоны:
        - Master: все поля обязательны
        - Slave: master_ip обязателен, остальные очищаются
        - Forward и Redirect: остаётся только forwarders, всё остальное очищается
        """
        cleaned_data = super().clean()
        zone_type = cleaned_data.get('zone_type')

        if zone_type == 'slave':
            cleaned_data['ns1'] = None
            cleaned_data['ns2'] = None
            cleaned_data['ttl'] = None
            cleaned_data['soa'] = None
            if not cleaned_data.get('master_ip'):
                self.add_error('master_ip', 'Необходимо указать master IP для slave зоны.')

        # Для forward и redirect зон
        if zone_type in ['forward', 'redirect']:
            cleaned_data['ns1'] = None
            cleaned_data['ns2'] = None
            cleaned_data['ttl'] = None
            cleaned_data['soa'] = None
            cleaned_data['master_ip'] = None
            if not cleaned_data.get('forwarders'):
                self.add_error('forwarders', 'Необходимо указать forwarders для этой зоны.')
                
        # Для master зон обязательны ns1, ns2, ttl и soa
        if zone_type == 'master':
            if not cleaned_data.get('ns1'):
                self.add_error('ns1', 'Необходимо указать NS1 для master зоны.')
            if not cleaned_data.get('ns2'):
                self.add_error('ns2', 'Необходимо указать NS2 для master зоны.')
            if not cleaned_data.get('ttl'):
                self.add_error('ttl', 'Необходимо указать TTL для master зоны.')
            if not cleaned_data.get('soa'):
                self.add_error('soa', 'Необходимо указать SOA для master зоны.')
        return cleaned_data