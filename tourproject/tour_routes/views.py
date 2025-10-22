import os
import json
import uuid
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import HttpResponse
from .forms import TourRouteForm
from xml.etree.ElementTree import Element, SubElement, tostring, parse, ParseError, ElementTree
from django.http import FileResponse, Http404

UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT)
ROUTES_XML = os.path.join(UPLOAD_DIR, 'routes.xml')

def index(request):
    return redirect('add_route')

def add_route(request):
    message = ''
    if request.method == 'POST':
        form = TourRouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            new_data = {
                'name': route.name,
                'description': route.description,
                'length_km': route.length_km,
                'difficulty': route.difficulty
            }
            # XML: читаем если есть или создаём корень
            if os.path.exists(ROUTES_XML):
                tree = ElementTree()
                tree.parse(ROUTES_XML)
                root = tree.getroot()
            else:
                root = Element('TourRoutes')
            route_elem = SubElement(root, 'TourRoute')
            for key, val in new_data.items():
                child = SubElement(route_elem, key)
                child.text = str(val)
            tree = ElementTree(root)
            tree.write(ROUTES_XML, encoding='utf-8', xml_declaration=True)

            message = "Маршрут добавлен"
            form = TourRouteForm()
        else:
            message = "Форма невалидна: " + str(form.errors)
    else:
        form = TourRouteForm()
    return render(request, 'tour_routes/add_route.html', {'form': form, 'message': message})

def upload_file(request):
    message = ''
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        # Санитайзим имя
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.xml']:
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
            if ext == '.xml':
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
                message = "файл с данными невалиден и удалён."
            else:
                message = f"файл {new_filename} успешно загружен."

    return render(request, 'tour_routes/upload_file.html', {'message': message})

def list_files(request):
    xml_files = []
    message = ''
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    for fname in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, fname)
        if fname.endswith('.xml'):
            xml_files.append(fname)

    if not xml_files:
        message = "файлы отсутствуют."

    files_data = []
    for fname in xml_files:
        try:
            tree = parse(os.path.join(UPLOAD_DIR, fname))
            root = tree.getroot()
            content = parse_xml_element(root)
            files_data.append({'filename': fname, 'content': content, 'format': 'XML'})
        except Exception:
            continue

    return render(request, 'tour_routes/list_files.html', {'files_data': files_data, 'message': message})


def parse_xml_element(element):
    if len(element) > 0:
        result = {}
        for child in element:
            child_data = parse_xml_element(child)
            
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    else:
        return element.text if element.text and element.text.strip() else None
def download_file(request, filename):
    safe_filename = filename  # Простейшая защита, можно доработать
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    else:
        raise Http404("файл не найден")