import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from documentsapi.models import *

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="testpass")

@pytest.fixture
def sample_documents(test_user, db):
    Document.objects.create(title="Report 1", content="Content 1", doc_type="report", status="approved", owner=test_user)
    Document.objects.create(title="Draft 1", content="Content 2", doc_type="report", status="draft", owner=test_user)
    Document.objects.create(title="Analysis", content="Security report", doc_type="analysis", status="approved", owner=test_user)

@pytest.mark.django_db
def test_filter_by_status(api_client, test_user, sample_documents):
    api_client.force_authenticate(user=test_user)
    response = api_client.get("/api/v1/documents/?status=approved")
    assert response.status_code == 200
    assert len(response.data) == 2

@pytest.mark.django_db
def test_filter_by_doc_type(api_client, test_user, sample_documents):
    api_client.force_authenticate(user=test_user)
    response = api_client.get("/api/v1/documents/?doc_type=report")
    assert response.status_code == 200
    assert len(response.data) == 2

@pytest.mark.django_db
def test_search_by_title(api_client, test_user, sample_documents):
    api_client.force_authenticate(user=test_user)
    response = api_client.get("/api/v1/documents/?search=Report")
    assert response.status_code == 200
    assert len(response.data) == 2  # "Report 1" и "Analysis"

@pytest.mark.django_db
def test_filter_by_created_at(api_client, test_user, sample_documents):
    api_client.force_authenticate(user=test_user)
    date = Document.objects.first().created_at.date()
    response = api_client.get(f"/api/v1/documents/?created_at={date}")
    assert response.status_code == 200
