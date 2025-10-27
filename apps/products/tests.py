from io import BytesIO
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from .models import Part


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




