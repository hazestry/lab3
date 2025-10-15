import os
import json
import uuid
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from .forms import TourRouteForm
from xml.etree.ElementTree import Element, SubElement, tostring, parse, ParseError

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT)

def index(request):
    return redirect('add_route')

def add_route(request):
    message = ''
    if request.method == 'POST':
        form = TourRouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            # Сохраняем в JSON и XML
            data = {
                'name': route.name,
                'description': route.description,
                'length_km': route.length_km,
                'difficulty': route.difficulty
            }
            # JSON
            json_filename = f"{uuid.uuid4()}.json"
            with open(os.path.join(UPLOAD_DIR, json_filename), 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)

            # XML
            root = Element('TourRoute')
            for key, val in data.items():
                child = SubElement(root, key)
                child.text = str(val)
            xml_filename = f"{uuid.uuid4()}.xml"
            with open(os.path.join(UPLOAD_DIR, xml_filename), 'wb') as xml_file:
                xml_file.write(tostring(root, encoding='utf-8'))

            message = "Маршрут сохранён в JSON и XML"
            form = TourRouteForm()  # очистить форму
        else:
            message = "Ошибка валидации формы"

    else:
        form = TourRouteForm()
    return render(request, 'tour_routes/add_route.html', {'form': form, 'message': message})

def upload_file(request):
    message = ''
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # Санитайзим имя
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.json', '.xml']:
            message = "Недопустимый формат файла"
        else:
            # Генерируем имя
            new_filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join(UPLOAD_DIR, new_filename)
            # Сохраняем файл
            with default_storage.open(filepath, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Проверка валидности
            is_valid = False
            if ext == '.json':
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Проверим наличие ключей (name, description, length_km, difficulty)
                    if all(k in data for k in ['name', 'description', 'length_km', 'difficulty']):
                        is_valid = True
                except Exception:
                    is_valid = False
            elif ext == '.xml':
                try:
                    tree = parse(filepath)
                    root = tree.getroot()
                    tags = [child.tag for child in root]
                    if all(tag in tags for tag in ['name', 'description', 'length_km', 'difficulty']):
                        is_valid = True
                except (ParseError, Exception):
                    is_valid = False

            if not is_valid:
                os.remove(filepath)
                message = "Файл с данными невалиден и удалён."
            else:
                message = f"Файл {new_filename} успешно загружен."

    return render(request, 'tour_routes/upload_file.html', {'message': message})

def list_files(request):
    json_files = []
    xml_files = []
    message = ''
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    for fname in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, fname)
        if fname.endswith('.json'):
            json_files.append(fname)
        elif fname.endswith('.xml'):
            xml_files.append(fname)

    if not json_files and not xml_files:
        message = "Файлы отсутствуют."

    files_data = []

    for fname in json_files:
        with open(os.path.join(UPLOAD_DIR, fname), 'r', encoding='utf-8') as f:
            content = json.load(f)
        files_data.append({'filename': fname, 'content': content, 'format': 'JSON'})

    for fname in xml_files:
        try:
            tree = parse(os.path.join(UPLOAD_DIR, fname))
            root = tree.getroot()
            content = {child.tag: child.text for child in root}
            files_data.append({'filename': fname, 'content': content, 'format': 'XML'})
        except Exception:
            continue

    return render(request, 'tour_routes/list_files.html', {'files_data': files_data, 'message': message})
