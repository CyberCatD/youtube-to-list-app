#!/usr/bin/env python3
"""
Phase 2 Verification Tests
Quick smoke tests to verify database and core functionality after Phase 2 changes.
Run with: python3 -m pytest tests/test_phase2_verification.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import inspect, text
from src.database import engine, SessionLocal, Base, SQLALCHEMY_DATABASE_URL
from src.models import (
    Recipe, Ingredient, RecipeIngredient, Instruction, Tag,
    GroceryList, GroceryListItem
)


class TestDatabaseConnection:
    """Test database connection and configuration."""
    
    def test_database_url_configured(self):
        """Verify database URL is properly configured."""
        assert SQLALCHEMY_DATABASE_URL is not None
        assert len(SQLALCHEMY_DATABASE_URL) > 0
        assert "sqlite" in SQLALCHEMY_DATABASE_URL or "postgresql" in SQLALCHEMY_DATABASE_URL
    
    def test_engine_connects(self):
        """Verify engine can connect to database."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_session_works(self):
        """Verify SessionLocal creates working sessions."""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        finally:
            db.close()


class TestAlembicMigrations:
    """Test Alembic migration setup."""
    
    def test_alembic_version_table_exists(self):
        """Verify alembic_version table was created."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "alembic_version" in tables
    
    def test_alembic_has_version(self):
        """Verify database has a migration version stamped."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            assert version is not None
            assert len(version[0]) > 0


class TestDatabaseIndexes:
    """Test performance indexes were created."""
    
    def test_recipes_category_index_exists(self):
        """Verify category index exists on recipes table."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("recipes")
        index_names = [idx["name"] for idx in indexes]
        assert "ix_recipes_category" in index_names
    
    def test_recipes_cuisine_index_exists(self):
        """Verify cuisine index exists on recipes table."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("recipes")
        index_names = [idx["name"] for idx in indexes]
        assert "ix_recipes_cuisine" in index_names
    
    def test_recipes_created_at_index_exists(self):
        """Verify created_at index exists on recipes table."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("recipes")
        index_names = [idx["name"] for idx in indexes]
        assert "ix_recipes_created_at" in index_names


class TestModels:
    """Test SQLAlchemy models load and work correctly."""
    
    def test_recipe_model_loads(self):
        """Verify Recipe model is properly configured."""
        assert Recipe.__tablename__ == "recipes"
        assert hasattr(Recipe, "id")
        assert hasattr(Recipe, "name")
        assert hasattr(Recipe, "category")
        assert hasattr(Recipe, "cuisine")
        assert hasattr(Recipe, "created_at")
    
    def test_ingredient_model_loads(self):
        """Verify Ingredient model is properly configured."""
        assert Ingredient.__tablename__ == "ingredients"
        assert hasattr(Ingredient, "id")
        assert hasattr(Ingredient, "name")
    
    def test_grocery_list_model_loads(self):
        """Verify GroceryList model is properly configured."""
        assert GroceryList.__tablename__ == "grocery_lists"
        assert hasattr(GroceryList, "id")
        assert hasattr(GroceryList, "name")
        assert hasattr(GroceryList, "items")
    
    def test_grocery_list_item_has_retail_fields(self):
        """Verify GroceryListItem has retail package fields."""
        assert hasattr(GroceryListItem, "retail_package")
        assert hasattr(GroceryListItem, "retail_package_count")
        assert hasattr(GroceryListItem, "exact_amount")


class TestDatabaseTables:
    """Test all expected tables exist."""
    
    def test_all_tables_exist(self):
        """Verify all model tables exist in database."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            "recipes",
            "ingredients", 
            "recipe_ingredients",
            "instructions",
            "tags",
            "recipe_tags",
            "grocery_lists",
            "grocery_list_items",
            "grocery_list_recipes",
            "alembic_version",
        ]
        
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"


class TestBasicQueries:
    """Test basic CRUD operations work."""
    
    def test_can_query_recipes(self):
        """Verify can query recipes table."""
        db = SessionLocal()
        try:
            recipes = db.query(Recipe).filter(Recipe.is_deleted == False).limit(5).all()
            assert isinstance(recipes, list)
        finally:
            db.close()
    
    def test_can_query_ingredients(self):
        """Verify can query ingredients table."""
        db = SessionLocal()
        try:
            ingredients = db.query(Ingredient).limit(5).all()
            assert isinstance(ingredients, list)
        finally:
            db.close()
    
    def test_can_query_grocery_lists(self):
        """Verify can query grocery_lists table."""
        db = SessionLocal()
        try:
            lists = db.query(GroceryList).limit(5).all()
            assert isinstance(lists, list)
        finally:
            db.close()
    
    def test_can_filter_by_category(self):
        """Verify category index is usable for queries."""
        db = SessionLocal()
        try:
            recipes = db.query(Recipe).filter(
                Recipe.category == "Dinner",
                Recipe.is_deleted == False
            ).all()
            assert isinstance(recipes, list)
        finally:
            db.close()
    
    def test_can_order_by_created_at(self):
        """Verify created_at index is usable for ordering."""
        db = SessionLocal()
        try:
            recipes = db.query(Recipe).filter(
                Recipe.is_deleted == False
            ).order_by(Recipe.created_at.desc()).limit(5).all()
            assert isinstance(recipes, list)
        finally:
            db.close()


class TestConfigModule:
    """Test config module loads correctly."""
    
    def test_config_loads(self):
        """Verify config module imports without error."""
        from src.config import GOOGLE_API_KEY, YOUTUBE_API_KEY, DEFAULT_RECIPE_LANGUAGE
        assert GOOGLE_API_KEY is not None
        assert YOUTUBE_API_KEY is not None
        assert DEFAULT_RECIPE_LANGUAGE == "English" or isinstance(DEFAULT_RECIPE_LANGUAGE, str)


class TestServicesImport:
    """Test service modules import correctly."""
    
    def test_recipe_service_imports(self):
        """Verify recipe_service module imports."""
        from src.services import recipe_service
        assert hasattr(recipe_service, "get_recipe_by_id")
    
    def test_grocery_list_service_imports(self):
        """Verify grocery_list_service module imports."""
        from src.services import grocery_list_service
        assert hasattr(grocery_list_service, "create_grocery_list")
        assert hasattr(grocery_list_service, "round_to_retail_package")
    
    def test_llm_service_imports(self):
        """Verify llm_service module imports."""
        from src.services import llm_service
        assert hasattr(llm_service, "generate_content_and_tags")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
