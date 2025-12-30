from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    source_url = Column(String, unique=True)
    
    prep_time = Column(String, nullable=True)
    cook_time = Column(String, nullable=True)
    total_time = Column(String, nullable=True)
    
    servings = Column(String, nullable=True)
    category = Column(String, nullable=True)
    cuisine = Column(String, nullable=True)
    calories = Column(Integer, nullable=True)
    main_image_url = Column(String, nullable=True) # New field for the main recipe image
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    instructions = relationship("Instruction", back_populates="recipe", cascade="all, delete-orphan")

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
