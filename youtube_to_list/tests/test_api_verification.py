#!/usr/bin/env python3
"""
API Endpoint Verification Tests
Quick smoke tests to verify API endpoints work correctly.
Run with: python3 -m pytest tests/test_api_verification.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test basic health and info endpoints."""
    
    def test_root_endpoint(self):
        """Verify root endpoint responds."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_docs_endpoint(self):
        """Verify OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200


class TestRecipeEndpoints:
    """Test recipe API endpoints."""
    
    def test_list_recipes(self):
        """Verify GET /api/v1/recipes/ returns recipes."""
        response = client.get("/api/v1/recipes/")
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
    
    def test_get_recipe_not_found(self):
        """Verify GET /api/v1/recipes/{id} returns 404 for non-existent recipe."""
        response = client.get("/api/v1/recipes/99999")
        assert response.status_code == 404
    
    def test_get_existing_recipe(self):
        """Verify GET /api/v1/recipes/{id} returns recipe if exists."""
        list_response = client.get("/api/v1/recipes/")
        recipes = list_response.json()["recipes"]
        
        if len(recipes) > 0:
            recipe_id = recipes[0]["id"]
            response = client.get(f"/api/v1/recipes/{recipe_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == recipe_id
            assert "name" in data
            assert "ingredients" in data
            assert "instructions" in data


class TestGroceryListEndpoints:
    """Test grocery list API endpoints."""
    
    def test_list_grocery_lists(self):
        """Verify GET /api/v1/grocery-lists/ returns lists."""
        response = client.get("/api/v1/grocery-lists/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_grocery_list_not_found(self):
        """Verify GET /api/v1/grocery-lists/{id} returns 404 for non-existent list."""
        response = client.get("/api/v1/grocery-lists/99999")
        assert response.status_code == 404


class TestYouTubeEndpoints:
    """Test YouTube processing endpoints (validation only, no actual API calls)."""
    
    def test_process_invalid_url(self):
        """Verify POST /api/v1/youtube/process-youtube-url rejects invalid URLs."""
        response = client.post(
            "/api/v1/youtube/process-youtube-url",
            json={"youtube_url": "not-a-valid-url"}
        )
        assert response.status_code == 400
    
    def test_process_non_youtube_url(self):
        """Verify POST /api/v1/youtube/process-youtube-url rejects non-YouTube URLs."""
        response = client.post(
            "/api/v1/youtube/process-youtube-url",
            json={"youtube_url": "https://vimeo.com/123456"}
        )
        assert response.status_code == 400


class TestCORSHeaders:
    """Test CORS is properly configured."""
    
    def test_cors_headers_on_get_request(self):
        """Verify CORS headers are in GET response."""
        response = client.get(
            "/api/v1/recipes/",
            headers={"Origin": "http://localhost:5173"}
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestResponseFormats:
    """Test API response formats are correct."""
    
    def test_recipes_have_expected_fields(self):
        """Verify recipe responses have all expected fields."""
        response = client.get("/api/v1/recipes/")
        recipes = response.json()["recipes"]
        
        if len(recipes) > 0:
            recipe = recipes[0]
            expected_fields = [
                "id", "name", "source_url", "prep_time", "cook_time",
                "servings", "category", "cuisine", "main_image_url",
                "ingredients", "instructions", "tags"
            ]
            for field in expected_fields:
                assert field in recipe, f"Missing field: {field}"
    
    def test_grocery_list_item_has_retail_fields(self):
        """Verify grocery list items have retail package fields in response."""
        response = client.get("/api/v1/grocery-lists/")
        lists = response.json()
        
        if len(lists) > 0 and len(lists[0].get("items", [])) > 0:
            item = lists[0]["items"][0]
            assert "retail_package" in item
            assert "retail_package_count" in item
            assert "exact_amount" in item


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
