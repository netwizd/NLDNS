from django.shortcuts import render, get_object_or_404, redirect
from .models import Zone, Record
from .forms import ZoneForm
from django.contrib import messages
from django.conf import settings
import os

# Отображение списка зон
def zone_list(request):
    zones = Zone.objects.all().order_by('-updated_at')  # Сортировка по дате последнего обновления
    return render(request, 'zones/zone_list.html', {'zones': zones})

# Детальная информация о зоне
def zone_detail(request, pk):
    # Получаем зону по первичному ключу
    zone = get_object_or_404(Zone, pk=pk)
    # Получаем все записи, связанные с этой зоной
    records = Record.objects.filter(zone=zone)

    # Передаём в шаблон зону и её записи
    return render(request, 'zones/zone_detail.html', {
        'zone': zone,
        'records': records
    })

# Создание новой зоны
def zone_create(request):
    if request.method == 'POST':
        form = ZoneForm(request.POST)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.serial += 1
            zone.save()

            # Генерация конфига BIND
            try:
                generate_bind_config(zone)
                print(f"[DEBUG] Конфиг создан для зоны: {zone.name}")
            except Exception as e:
                print(f"[ERROR] Ошибка генерации конфига: {e}")

            messages.success(request, 'Zone successfully created!')
            return redirect('zone_list')
        else:
            # Вывод ошибок формы
            print(f"[ERROR] Ошибки в форме: {form.errors}")
            messages.error(request, 'Ошибка в заполнении формы.')
    else:
        form = ZoneForm()

    return render(request, 'zones/zone_form.html', {'form': form, 'edit_mode': False})

# Редактирование зоны
def zone_update(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            zone = form.save(commit=False)
            zone.serial += 1
            zone.save()

            # Генерация конфига BIND
            try:
                generate_bind_config(zone)
                print(f"[DEBUG] Конфиг обновлен для зоны: {zone.name}")
            except Exception as e:
                print(f"[ERROR] Ошибка обновления конфига: {e}")

            messages.success(request, 'Zone successfully updated!')
            return redirect('zone_detail', pk=zone.pk)
        else:
            print(f"[ERROR] Ошибки в форме: {form.errors}")
            messages.error(request, 'Ошибка в заполнении формы.')
    else:
        form = ZoneForm(instance=zone)

    return render(request, 'zones/zone_form.html', {'form': form, 'edit_mode': True})

# Удаление зоны
def zone_delete(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    
    if request.method == 'POST':
        # Определяем путь к файлу зоны
        if zone.zone_type == 'slave':
            zone_file = os.path.join(settings.BIND_ZONES_PATH, "slave", f"{zone.name}.conf")
        elif zone.zone_type in ['forward', 'redirect']:
            zone_file = os.path.join(settings.BIND_ZONES_PATH, "forward", f"{zone.name}.conf")
        else:
            zone_file = os.path.join(settings.BIND_ZONES_PATH, "master", f"db.{zone.name}")
            # Удаляем связанный PTR файл
            ptr_file = os.path.join(settings.BIND_ZONES_PATH, "reverse", f"db.{zone.name}")
            if os.path.exists(ptr_file):
                os.remove(ptr_file)

        # Удаляем файл зоны
        if os.path.exists(zone_file):
            os.remove(zone_file)
        
        # Удаляем запись из БД
        zone.delete()

        messages.success(request, 'Zone successfully deleted!')
        return redirect('zone_list')

    return render(request, 'zones/zone_confirm_delete.html', {'zone': zone})

# Функция генерации конфигурации BIND
def generate_bind_config(zone):
    """
    Генерация конфигурации BIND в зависимости от типа зоны
    """
    # Путь к зонам
    master_path = os.path.join(settings.BIND_ZONES_PATH, "master")
    slave_path = os.path.join(settings.BIND_ZONES_PATH, "slave")
    forward_path = os.path.join(settings.BIND_ZONES_PATH, "forward")
    reverse_path = os.path.join(settings.BIND_ZONES_PATH, "reverse")

    # Проверяем и создаем каталоги, если их нет
    os.makedirs(master_path, exist_ok=True)
    os.makedirs(slave_path, exist_ok=True)
    os.makedirs(forward_path, exist_ok=True)
    os.makedirs(reverse_path, exist_ok=True)

    if zone.zone_type == 'master':
        # Создаем Master зону
        zone_file_path = os.path.join(master_path, f"db.{zone.name}.conf")
        zone_template = f"""
$TTL {zone.ttl}
@   IN  SOA ns1.{zone.name}. {zone.soa} (
        {zone.serial} ; Serial
        3600     ; Refresh
        1800     ; Retry
        1209600  ; Expire
        86400    ; Minimum TTL
)
    IN  NS  {zone.ns1}.
    IN  NS  {zone.ns2}.
"""
        with open(zone_file_path, 'w') as zone_file:
            zone_file.write(zone_template)

    elif zone.zone_type == 'slave':
        # Создаем Slave зону
        zone_file_path = os.path.join(slave_path, f"{zone.name}.conf")
        zone_template = f"""
zone "{zone.name}" {{
    type slave;
    masters {{ {zone.master_ip}; }};
    file "{settings.BIND_ZONES_PATH}/db.{zone.name}";
}};
"""
        with open(zone_file_path, 'w') as zone_file:
            zone_file.write(zone_template)

    elif zone.zone_type in ['forward', 'redirect']:
        forward_type = "first" if zone.zone_type == 'forward' else "only"
        zone_file_path = os.path.join(forward_path, f"{zone.name}.conf")
        zone_template = f"""
zone "{zone.name}" {{
    type forward;
    forward {forward_type};
    forwarders {{ {zone.forwarders}; }};
}};
"""
        with open(zone_file_path, 'w') as zone_file:
            zone_file.write(zone_template)

    print(f"[DEBUG] Конфиг создан: {zone_file_path}")