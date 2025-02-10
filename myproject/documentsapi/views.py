import logging
import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import JSONParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document
from .serializers import DocumentSerializer

logger = logging.getLogger('api')


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['doc_type', 'status', 'created_at']
    search_fields = ['title', 'content']

    def perform_create(self, serializer):
        try:
            document = serializer.save(owner=self.request.user)
            self._save_document_to_file(document)
            logger.info(f"Документ {document.id} успешно создан пользователем {self.request.user}")
        except Exception as e:
            logger.error(f"Ошибка при создании документа: {str(e)}")
            raise

    def update(self, request, *args, **kwargs):
        """Обновление документа с записью в файл"""
        try:
            response = super().update(request, *args, **kwargs)
            document = self.get_object()
            self._save_document_to_file(document)
            logger.info(f"Документ {document.id} обновлён пользователем {request.user}")
            return response
        except ObjectDoesNotExist:
            logger.warning("Документ не найден")
            return Response({"error": "Документ не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Ошибка обновления документа: {str(e)}")
            return Response({"error": "Ошибка обновления"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Удаление документа с логированием"""
        try:
            document = self.get_object()
            doc_path = self._get_document_path(document.id)
            if os.path.exists(doc_path):
                os.remove(doc_path)
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Документ {document.id} удалён пользователем {request.user}")
            return response
        except ObjectDoesNotExist:
            logger.warning("Документ не найден")
            return Response({"error": "Документ не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {str(e)}")
            return Response({"error": "Ошибка удаления"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _save_document_to_file(self, document):
        """Сохраняет документ в текстовый файл в директории `documents/`"""
        directory = os.path.join(settings.MEDIA_ROOT, 'documents')
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"{document.id}.txt")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"Title: {document.title}\n")
            file.write(f"Type: {document.doc_type}\n")
            file.write(f"Status: {document.status}\n")
            file.write(f"Created At: {document.created_at}\n")
            file.write(f"Owner: {document.owner.username}\n")
            file.write("\n--- Content ---\n")
            file.write(document.content)
        logger.info(f"Документ {document.id} сохранён в файл: {file_path}")

    def _get_document_path(self, document_id):
        """Получает путь к файлу документа"""
        return os.path.join(settings.MEDIA_ROOT, 'documents', f"{document_id}.txt")

    @swagger_auto_schema(method='get', manual_parameters=[
        openapi.Parameter('status', openapi.IN_QUERY, description="Фильтр по статусу", type=openapi.TYPE_STRING),
    ])
    @action(detail=False, methods=['get'])
    def filter_by_status(self, request):
        """Фильтр документов по статусу"""
        try:
            status_value = request.query_params.get('status', None)
            if status_value:
                docs = self.queryset.filter(status=status_value)
            else:
                docs = self.queryset
            serializer = self.get_serializer(docs, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Ошибка фильтрации документов: {str(e)}")
            return Response({"error": "Ошибка фильтрации"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
