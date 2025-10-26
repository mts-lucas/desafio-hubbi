from rest_framework import status
from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Part
from .permissions import IsAdminOrReadOnly
from .serializers import PartDetailSerializer, PartListSerializer
from .tasks import import_parts_from_csv


class PartListView(ListCreateAPIView):
    """
    Permite Listar e Cadastrar Peças.
    """
    queryset = Part.objects.all()
    permission_classes = [IsAdminOrReadOnly,]
    serializer_class = PartListSerializer


class PartDetailView(RetrieveUpdateDestroyAPIView):
    """
    Permite Visualizar, Editar e Remover Peças.
    """
    queryset = Part.objects.all()
    permission_classes = [IsAdminOrReadOnly,]
    serializer_class = PartDetailSerializer


class PartImportView(APIView):
    """
    Endpoint para que usuários admin possam fazer upload de planilha
    para popular peças.
    """
    permission_classes = [IsAdminOrReadOnly,]
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"detail": "file required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_content = file.read().decode("utf-8")
        import_parts_from_csv.delay(csv_content)

        return Response(
            {
                "detail": "Importação agendada com sucesso.",
                "message": "O arquivo foi recebido e está sendo processado em background.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


