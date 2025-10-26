import csv
from io import StringIO

from celery import shared_task

from .models import Part


@shared_task
def import_parts_from_csv(csv_text):
    f = StringIO(csv_text)
    reader = csv.DictReader(f)
    created = 0
    for row in reader:
        Part.objects.create(
            name=row.get('name') or row.get('nome'),
            description=row.get('description') or row.get('descricao',''),
            price=row.get('price') or row.get('preco') or 0,
            quantity=int(row.get('quantity') or row.get('quantidade') or 0)
        )
        created += 1
    return {'created': created}


@shared_task
def replenish_stock_minimum(minimum=10):
    parts = Part.objects.filter(quantity__lt=minimum)
    updated = []
    for p in parts:
        p.quantity = minimum
        p.save()
        updated.append(p.id)
    
    return {'updated_count': len(updated)}