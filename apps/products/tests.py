from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Part
from .tasks import import_parts_from_csv, replenish_stock_minimum


class PartViewsTest(APITestCase):
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin", password="pass")
        self.regular_user = User.objects.create_user(username="user", password="pass")
        self.part1 = Part.objects.create(name="Peça 1", description="Desc 1", price=10.0, quantity=5)
        self.part2 = Part.objects.create(name="Peça 2", description="Desc 2", price=20.0, quantity=10)


    def test_list_parts_authenticated(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_parts_unauthenticated(self):
        url = reverse("part-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_part_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-list")
        data = {"name": "Nova Peça", "description": "Nova desc", "price": 15.0, "quantity": 7}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Part.objects.count(), 3)

    def test_create_part_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-list")
        data = {"name": "Nova Peça", "description": "Nova desc", "price": 15.0, "quantity": 7}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_retrieve_part(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-detail", args=[self.part1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.part1.name)

    def test_retrieve_part_unauthenticated(self):
        url = reverse("part-detail", args=[self.part1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_part_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-detail", args=[self.part1.id])
        data = {"name": "Peça Atualizada", "description": "Desc Atualizada", "price": 50.0, "quantity": 8}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Peça Atualizada")

    def test_update_part_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-detail", args=[self.part1.id])
        data = {"name": "Peça Atualizada", "description": "Desc Atualizada", "price": 50.0, "quantity": 8}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_part_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-detail", args=[self.part1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Part.objects.filter(id=self.part1.id).exists())

    def test_delete_part_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-detail", args=[self.part1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Part.objects.filter(id=self.part1.id).exists())


    @patch("apps.products.views.import_parts_from_csv.delay")
    def test_import_csv_admin_file(self, mock_task):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-import")

        with open("docs/planilha.csv", "rb") as f:
            data = {"file": f}
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once()
        self.assertIn("detail", response.data)

    @patch("apps.products.views.import_parts_from_csv.delay")
    def test_import_csv_invalid_file(self, mock_task):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-import")

        # CSV inválido (por exemplo, altere o cabeçalho)
        with open("docs/planilha.csv", "rb") as f:
            # Simulando arquivo inválido renomeando o conteúdo
            content = f.read().replace(b"nome", b"nome_errado")
            from io import BytesIO
            data = {"file": BytesIO(content)}
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_task.assert_not_called()

    def test_import_csv_missing_file(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("part-import")
        response = self.client.post(url, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_import_csv_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("part-import")

        with open("docs/planilha.csv", "rb") as f:
            data = {"file": f}
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_import_csv_unauthenticated(self):
        url = reverse("part-import")
        with open("docs/planilha.csv", "rb") as f:
            data = {"file": f}
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PartTasksTest(TestCase):
    def setUp(self):
        self.existing_part = Part.objects.create(
            name="Peça Existente",
            description="Descrição antiga",
            price=20,
            quantity=5
        )
        
        self.csv_path = Path("docs/planilha.csv")


    def test_import_csv_creates_and_updates(self):
        csv_text = """name,description,price,quantity
Part New,New Desc,30,3
Peça Existente,Updated Desc,20,8
,Missing Name,15,2
Part Invalid,Invalid Price,abc,5
"""
        result = import_parts_from_csv(csv_text)

        self.assertEqual(result["created"], 1)   
        self.assertEqual(result["updated"], 1)   
        self.assertEqual(result["skipped"], 2)  
        self.assertEqual(result["total"], 4)

        updated_part = Part.objects.get(name="Peça Existente")
        self.assertEqual(updated_part.price, 20.00)
        self.assertEqual(updated_part.quantity, 8)
        new_part = Part.objects.get(name="Part New")
        self.assertEqual(new_part.description, "New Desc")

    def test_import_csv_empty(self):
        csv_text = "nome,descricao,preco,quantidade\n"
        result = import_parts_from_csv(csv_text)
        self.assertEqual(result, {"created": 0, "updated": 0, "skipped": 0, "total": 0})

    def test_import_csv_from_real_file(self):

        if not self.csv_path.exists():
            self.skipTest("Arquivo docs/planilha.csv não encontrado.")

        csv_text = self.csv_path.read_text(encoding="utf-8")
        result = import_parts_from_csv(csv_text)

        self.assertIn("created", result)
        self.assertIn("updated", result)
        self.assertIn("skipped", result)
        self.assertIn("total", result)

        self.assertGreaterEqual(result["created"], 0)
        self.assertGreaterEqual(result["total"], result["created"] + result["updated"] + result["skipped"])

        first_line = csv_text.splitlines()[1]
        name = first_line.split(",")[0]
        self.assertTrue(Part.objects.filter(name=name).exists())


    def test_replenish_stock_minimum_updates_parts(self):
        Part.objects.create(name="Baixa 1", description="", price=5.0, quantity=2)
        Part.objects.create(name="Baixa 2", description="", price=10.0, quantity=0)
        Part.objects.create(name="Alta", description="", price=15.0, quantity=15)

        result = replenish_stock_minimum(minimum=10)
        self.assertEqual(result["updated_count"], 3)

        for p in Part.objects.all():
            self.assertGreaterEqual(p.quantity, 10)

    def test_replenish_stock_minimum_no_update_needed(self):
        Part.objects.create(name="Alta 1", description="", price=5, quantity=12)
        Part.objects.create(name="Alta 2", description="", price=10, quantity=15)

        result = replenish_stock_minimum(minimum=10)
        # ja existe um criado no setup
        self.assertEqual(result["updated_count"], 1)

        for p in Part.objects.all():
            self.assertGreaterEqual(p.quantity, 10)





