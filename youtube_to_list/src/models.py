from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Text, Table, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# Association table for recipe tags (many-to-many)
recipe_tags = Table(
    'recipe_tags',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    source_url = Column(String, unique=True)
    source_type = Column(String, nullable=True, default="youtube")  # youtube, web, instagram, tiktok
    
    prep_time = Column(String, nullable=True)
    cook_time = Column(String, nullable=True)
    total_time = Column(String, nullable=True)
    
    servings = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    cuisine = Column(String, nullable=True, index=True)
    calories = Column(Integer, nullable=True)
    main_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    instructions = relationship("Instruction", back_populates="recipe", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=recipe_tags, back_populates="recipes")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    recipes = relationship("RecipeIngredient", back_populates="ingredient")

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")

class Instruction(Base):
    __tablename__ = "instructions"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    section_name = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    
    # Relationship
    recipe = relationship("Recipe", back_populates="instructions")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    tag_type = Column(String, nullable=False)  # 'ingredient', 'cuisine', 'category', etc.
    
    # Relationship
    recipes = relationship("Recipe", secondary=recipe_tags, back_populates="tags")


# Association table for grocery list recipes (many-to-many)
grocery_list_recipes = Table(
    'grocery_list_recipes',
    Base.metadata,
    Column('grocery_list_id', Integer, ForeignKey('grocery_lists.id', ondelete='CASCADE'), primary_key=True),
    Column('recipe_id', Integer, ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True)
)


class GroceryList(Base):
    __tablename__ = "grocery_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="My Grocery List")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("GroceryListItem", back_populates="grocery_list", cascade="all, delete-orphan")
    recipes = relationship("Recipe", secondary=grocery_list_recipes)


class GroceryListItem(Base):
    __tablename__ = "grocery_list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    grocery_list_id = Column(Integer, ForeignKey("grocery_lists.id", ondelete="CASCADE"), nullable=False)
    
    ingredient_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    category = Column(String, nullable=True)  # Produce, Dairy, Meat, Pantry, etc.
    is_checked = Column(Boolean, default=False, nullable=False)
    recipe_ids = Column(JSON, nullable=True)  # Array of recipe IDs that need this ingredient
    
    retail_package = Column(String, nullable=True)  # e.g., "1/2 gallon", "1 dozen"
    retail_package_count = Column(Integer, nullable=True)  # Number of packages needed
    exact_amount = Column(String, nullable=True)  # e.g., "0.42 cup", "4 needed"
    
    # Relationship
    grocery_list = relationship("GroceryList", back_populates="items")
