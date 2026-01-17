import re
from typing import Dict, Any, Optional, List
from urllib.parse import quote
import requests

from src.logging_config import get_logger
from src.config import settings

logger = get_logger(__name__)

USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"
USDA_API_KEY = settings.usda_api_key

NUTRIENT_IDS = {
    "calories": 1008,
    "protein": 1003,
    "carbs": 1005,
    "fat": 1004,
    "fiber": 1079,
    "sugar": 2000,
    "sodium": 1093,
    "cholesterol": 1253,
    "saturated_fat": 1258,
}

UNIT_CONVERSIONS_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "oz": 28.35,
    "ounce": 28.35,
    "ounces": 28.35,
    "lb": 453.592,
    "lbs": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "ml": 1.0,
    "milliliter": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "pint": 473.0,
    "quart": 946.0,
    "gallon": 3785.0,
    "piece": 100.0,
    "pieces": 100.0,
    "slice": 30.0,
    "slices": 30.0,
    "clove": 3.0,
    "cloves": 3.0,
    "large": 50.0,
    "medium": 40.0,
    "small": 30.0,
    "pinch": 0.5,
    "dash": 0.5,
    "bunch": 100.0,
    "sprig": 2.0,
    "sprigs": 2.0,
    "stalk": 50.0,
    "stalks": 50.0,
    "head": 500.0,
    "can": 400.0,
    "package": 200.0,
    "pkg": 200.0,
    "stick": 113.0,
    "block": 400.0,
}

nutrition_cache: Dict[str, Dict[str, Any]] = {}

COMMON_FOODS_DB: Dict[str, Dict[str, Any]] = {
    "egg": {"description": "Egg, whole, raw", "calories": 143, "protein": 12.6, "carbs": 0.7, "fat": 9.5, "fiber": 0, "sugar": 0.4, "sodium": 142},
    "eggs": {"description": "Egg, whole, raw", "calories": 143, "protein": 12.6, "carbs": 0.7, "fat": 9.5, "fiber": 0, "sugar": 0.4, "sodium": 142},
    "butter": {"description": "Butter, salted", "calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81.1, "fiber": 0, "sugar": 0.1, "sodium": 643},
    "salt": {"description": "Salt, table", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 38758},
    "sugar": {"description": "Sugar, granulated", "calories": 387, "protein": 0, "carbs": 100, "fat": 0, "fiber": 0, "sugar": 100, "sodium": 1},
    "flour": {"description": "Flour, all-purpose", "calories": 364, "protein": 10.3, "carbs": 76.3, "fat": 1.0, "fiber": 2.7, "sugar": 0.3, "sodium": 2},
    "all-purpose flour": {"description": "Flour, all-purpose", "calories": 364, "protein": 10.3, "carbs": 76.3, "fat": 1.0, "fiber": 2.7, "sugar": 0.3, "sodium": 2},
    "milk": {"description": "Milk, whole", "calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0, "sugar": 5.0, "sodium": 43},
    "whole milk": {"description": "Milk, whole", "calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "fiber": 0, "sugar": 5.0, "sodium": 43},
    "olive oil": {"description": "Oil, olive", "calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 2},
    "vegetable oil": {"description": "Oil, vegetable", "calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
    "oil": {"description": "Oil, vegetable", "calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
    "chicken breast": {"description": "Chicken breast, raw", "calories": 120, "protein": 22.5, "carbs": 0, "fat": 2.6, "fiber": 0, "sugar": 0, "sodium": 74},
    "chicken": {"description": "Chicken, raw", "calories": 215, "protein": 18.6, "carbs": 0, "fat": 15.1, "fiber": 0, "sugar": 0, "sodium": 70},
    "beef": {"description": "Beef, ground, raw", "calories": 254, "protein": 17.2, "carbs": 0, "fat": 20.0, "fiber": 0, "sugar": 0, "sodium": 66},
    "ground beef": {"description": "Beef, ground, raw", "calories": 254, "protein": 17.2, "carbs": 0, "fat": 20.0, "fiber": 0, "sugar": 0, "sodium": 66},
    "pork": {"description": "Pork, raw", "calories": 242, "protein": 17.0, "carbs": 0, "fat": 19.0, "fiber": 0, "sugar": 0, "sodium": 62},
    "salmon": {"description": "Salmon, raw", "calories": 208, "protein": 20.4, "carbs": 0, "fat": 13.4, "fiber": 0, "sugar": 0, "sodium": 59},
    "tuna": {"description": "Tuna, canned in water", "calories": 116, "protein": 25.5, "carbs": 0, "fat": 0.8, "fiber": 0, "sugar": 0, "sodium": 338},
    "canned tuna": {"description": "Tuna, canned in water", "calories": 116, "protein": 25.5, "carbs": 0, "fat": 0.8, "fiber": 0, "sugar": 0, "sodium": 338},
    "rice": {"description": "Rice, white, cooked", "calories": 130, "protein": 2.7, "carbs": 28.2, "fat": 0.3, "fiber": 0.4, "sugar": 0, "sodium": 1},
    "white rice": {"description": "Rice, white, cooked", "calories": 130, "protein": 2.7, "carbs": 28.2, "fat": 0.3, "fiber": 0.4, "sugar": 0, "sodium": 1},
    "pasta": {"description": "Pasta, cooked", "calories": 131, "protein": 5.0, "carbs": 25.0, "fat": 1.1, "fiber": 1.8, "sugar": 0.6, "sodium": 1},
    "potato": {"description": "Potato, raw", "calories": 77, "protein": 2.0, "carbs": 17.5, "fat": 0.1, "fiber": 2.2, "sugar": 0.8, "sodium": 6},
    "potatoes": {"description": "Potato, raw", "calories": 77, "protein": 2.0, "carbs": 17.5, "fat": 0.1, "fiber": 2.2, "sugar": 0.8, "sodium": 6},
    "onion": {"description": "Onion, raw", "calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1, "fiber": 1.7, "sugar": 4.2, "sodium": 4},
    "onions": {"description": "Onion, raw", "calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1, "fiber": 1.7, "sugar": 4.2, "sodium": 4},
    "spring onion": {"description": "Onion, spring/scallion", "calories": 32, "protein": 1.8, "carbs": 7.3, "fat": 0.2, "fiber": 2.6, "sugar": 2.3, "sodium": 16},
    "spring onions": {"description": "Onion, spring/scallion", "calories": 32, "protein": 1.8, "carbs": 7.3, "fat": 0.2, "fiber": 2.6, "sugar": 2.3, "sodium": 16},
    "garlic": {"description": "Garlic, raw", "calories": 149, "protein": 6.4, "carbs": 33.1, "fat": 0.5, "fiber": 2.1, "sugar": 1.0, "sodium": 17},
    "tomato": {"description": "Tomato, raw", "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "sugar": 2.6, "sodium": 5},
    "tomatoes": {"description": "Tomato, raw", "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "fiber": 1.2, "sugar": 2.6, "sodium": 5},
    "carrot": {"description": "Carrot, raw", "calories": 41, "protein": 0.9, "carbs": 9.6, "fat": 0.2, "fiber": 2.8, "sugar": 4.7, "sodium": 69},
    "carrots": {"description": "Carrot, raw", "calories": 41, "protein": 0.9, "carbs": 9.6, "fat": 0.2, "fiber": 2.8, "sugar": 4.7, "sodium": 69},
    "celery": {"description": "Celery, raw", "calories": 14, "protein": 0.7, "carbs": 3.0, "fat": 0.2, "fiber": 1.6, "sugar": 1.3, "sodium": 80},
    "broccoli": {"description": "Broccoli, raw", "calories": 34, "protein": 2.8, "carbs": 7.0, "fat": 0.4, "fiber": 2.6, "sugar": 1.7, "sodium": 33},
    "spinach": {"description": "Spinach, raw", "calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "sugar": 0.4, "sodium": 79},
    "lettuce": {"description": "Lettuce, raw", "calories": 15, "protein": 1.4, "carbs": 2.9, "fat": 0.2, "fiber": 1.3, "sugar": 0.8, "sodium": 28},
    "cheese": {"description": "Cheese, cheddar", "calories": 403, "protein": 22.9, "carbs": 3.4, "fat": 33.3, "fiber": 0, "sugar": 0.5, "sodium": 653},
    "cheddar": {"description": "Cheese, cheddar", "calories": 403, "protein": 22.9, "carbs": 3.4, "fat": 33.3, "fiber": 0, "sugar": 0.5, "sodium": 653},
    "parmesan": {"description": "Cheese, parmesan", "calories": 431, "protein": 38.5, "carbs": 4.1, "fat": 28.6, "fiber": 0, "sugar": 0.9, "sodium": 1529},
    "mozzarella": {"description": "Cheese, mozzarella", "calories": 280, "protein": 27.5, "carbs": 3.1, "fat": 17.1, "fiber": 0, "sugar": 1.0, "sodium": 627},
    "cream cheese": {"description": "Cream cheese", "calories": 342, "protein": 5.9, "carbs": 4.1, "fat": 34.2, "fiber": 0, "sugar": 3.8, "sodium": 321},
    "sour cream": {"description": "Sour cream", "calories": 193, "protein": 2.4, "carbs": 4.6, "fat": 19.4, "fiber": 0, "sugar": 3.5, "sodium": 53},
    "yogurt": {"description": "Yogurt, plain", "calories": 61, "protein": 3.5, "carbs": 4.7, "fat": 3.3, "fiber": 0, "sugar": 4.7, "sodium": 46},
    "cream": {"description": "Cream, heavy", "calories": 340, "protein": 2.1, "carbs": 2.8, "fat": 36.1, "fiber": 0, "sugar": 2.9, "sodium": 27},
    "heavy cream": {"description": "Cream, heavy", "calories": 340, "protein": 2.1, "carbs": 2.8, "fat": 36.1, "fiber": 0, "sugar": 2.9, "sodium": 27},
    "mayonnaise": {"description": "Mayonnaise", "calories": 680, "protein": 1.0, "carbs": 0.6, "fat": 75.0, "fiber": 0, "sugar": 0.6, "sodium": 635},
    "mustard": {"description": "Mustard, prepared", "calories": 66, "protein": 4.4, "carbs": 5.8, "fat": 4.0, "fiber": 3.3, "sugar": 2.2, "sodium": 1135},
    "ketchup": {"description": "Ketchup", "calories": 101, "protein": 1.0, "carbs": 27.4, "fat": 0.1, "fiber": 0.3, "sugar": 21.3, "sodium": 907},
    "soy sauce": {"description": "Soy sauce", "calories": 53, "protein": 8.1, "carbs": 4.9, "fat": 0.0, "fiber": 0.8, "sugar": 0.4, "sodium": 5493},
    "honey": {"description": "Honey", "calories": 304, "protein": 0.3, "carbs": 82.4, "fat": 0, "fiber": 0.2, "sugar": 82.1, "sodium": 4},
    "maple syrup": {"description": "Maple syrup", "calories": 260, "protein": 0, "carbs": 67.0, "fat": 0.1, "fiber": 0, "sugar": 60.5, "sodium": 12},
    "vanilla extract": {"description": "Vanilla extract", "calories": 288, "protein": 0.1, "carbs": 12.7, "fat": 0.1, "fiber": 0, "sugar": 12.7, "sodium": 9},
    "vanilla": {"description": "Vanilla extract", "calories": 288, "protein": 0.1, "carbs": 12.7, "fat": 0.1, "fiber": 0, "sugar": 12.7, "sodium": 9},
    "baking powder": {"description": "Baking powder", "calories": 53, "protein": 0, "carbs": 27.7, "fat": 0, "fiber": 0.2, "sugar": 0, "sodium": 10600},
    "baking soda": {"description": "Baking soda", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 27360},
    "yeast": {"description": "Yeast, baker's", "calories": 325, "protein": 40.4, "carbs": 41.2, "fat": 7.6, "fiber": 26.9, "sugar": 0, "sodium": 51},
    "breadcrumbs": {"description": "Breadcrumbs, dry", "calories": 395, "protein": 13.4, "carbs": 72.0, "fat": 5.3, "fiber": 4.5, "sugar": 6.2, "sodium": 732},
    "bread crumbs": {"description": "Breadcrumbs, dry", "calories": 395, "protein": 13.4, "carbs": 72.0, "fat": 5.3, "fiber": 4.5, "sugar": 6.2, "sodium": 732},
    "bread": {"description": "Bread, white", "calories": 265, "protein": 9.4, "carbs": 49.0, "fat": 3.2, "fiber": 2.7, "sugar": 5.0, "sodium": 491},
    "lemon": {"description": "Lemon, raw", "calories": 29, "protein": 1.1, "carbs": 9.3, "fat": 0.3, "fiber": 2.8, "sugar": 2.5, "sodium": 2},
    "lemon juice": {"description": "Lemon juice", "calories": 22, "protein": 0.4, "carbs": 6.9, "fat": 0.2, "fiber": 0.3, "sugar": 2.5, "sodium": 1},
    "lemon zest": {"description": "Lemon peel", "calories": 47, "protein": 1.5, "carbs": 16.0, "fat": 0.3, "fiber": 10.6, "sugar": 4.2, "sodium": 6},
    "lime": {"description": "Lime, raw", "calories": 30, "protein": 0.7, "carbs": 10.5, "fat": 0.2, "fiber": 2.8, "sugar": 1.7, "sodium": 2},
    "orange": {"description": "Orange, raw", "calories": 47, "protein": 0.9, "carbs": 11.8, "fat": 0.1, "fiber": 2.4, "sugar": 9.4, "sodium": 0},
    "apple": {"description": "Apple, raw", "calories": 52, "protein": 0.3, "carbs": 13.8, "fat": 0.2, "fiber": 2.4, "sugar": 10.4, "sodium": 1},
    "banana": {"description": "Banana, raw", "calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "fiber": 2.6, "sugar": 12.2, "sodium": 1},
    "chocolate chips": {"description": "Chocolate chips, semisweet", "calories": 479, "protein": 4.2, "carbs": 63.1, "fat": 29.7, "fiber": 5.9, "sugar": 54.5, "sodium": 10},
    "chocolate": {"description": "Chocolate, dark", "calories": 546, "protein": 5.5, "carbs": 59.4, "fat": 32.4, "fiber": 7.0, "sugar": 47.9, "sodium": 6},
    "cocoa": {"description": "Cocoa powder", "calories": 228, "protein": 19.6, "carbs": 57.9, "fat": 13.7, "fiber": 37.0, "sugar": 1.8, "sodium": 21},
    "cocoa powder": {"description": "Cocoa powder", "calories": 228, "protein": 19.6, "carbs": 57.9, "fat": 13.7, "fiber": 37.0, "sugar": 1.8, "sodium": 21},
    "brown sugar": {"description": "Sugar, brown", "calories": 380, "protein": 0.1, "carbs": 98.1, "fat": 0, "fiber": 0, "sugar": 97.0, "sodium": 28},
    "white sugar": {"description": "Sugar, granulated", "calories": 387, "protein": 0, "carbs": 100, "fat": 0, "fiber": 0, "sugar": 100, "sodium": 1},
    "powdered sugar": {"description": "Sugar, powdered", "calories": 389, "protein": 0, "carbs": 99.8, "fat": 0, "fiber": 0, "sugar": 97.8, "sodium": 2},
    "walnuts": {"description": "Walnuts", "calories": 654, "protein": 15.2, "carbs": 13.7, "fat": 65.2, "fiber": 6.7, "sugar": 2.6, "sodium": 2},
    "almonds": {"description": "Almonds", "calories": 579, "protein": 21.2, "carbs": 21.6, "fat": 49.9, "fiber": 12.5, "sugar": 4.4, "sodium": 1},
    "peanuts": {"description": "Peanuts", "calories": 567, "protein": 25.8, "carbs": 16.1, "fat": 49.2, "fiber": 8.5, "sugar": 4.7, "sodium": 18},
    "tofu": {"description": "Tofu, firm", "calories": 144, "protein": 15.6, "carbs": 2.8, "fat": 8.7, "fiber": 1.9, "sugar": 0.6, "sodium": 14},
    "bacon": {"description": "Bacon, cooked", "calories": 541, "protein": 37.0, "carbs": 1.4, "fat": 42.0, "fiber": 0, "sugar": 0, "sodium": 1717},
    "ham": {"description": "Ham, sliced", "calories": 145, "protein": 20.9, "carbs": 1.5, "fat": 5.5, "fiber": 0, "sugar": 0, "sodium": 1203},
    "sausage": {"description": "Sausage, pork", "calories": 339, "protein": 19.4, "carbs": 0, "fat": 28.4, "fiber": 0, "sugar": 0, "sodium": 749},
    "shrimp": {"description": "Shrimp, raw", "calories": 85, "protein": 20.1, "carbs": 0.2, "fat": 0.5, "fiber": 0, "sugar": 0, "sodium": 119},
    "crab": {"description": "Crab, cooked", "calories": 97, "protein": 19.4, "carbs": 0, "fat": 1.5, "fiber": 0, "sugar": 0, "sodium": 395},
    "lobster": {"description": "Lobster, cooked", "calories": 89, "protein": 19.0, "carbs": 0.5, "fat": 0.9, "fiber": 0, "sugar": 0, "sodium": 486},
    "parsley": {"description": "Parsley, fresh", "calories": 36, "protein": 3.0, "carbs": 6.3, "fat": 0.8, "fiber": 3.3, "sugar": 0.9, "sodium": 56},
    "cilantro": {"description": "Cilantro, fresh", "calories": 23, "protein": 2.1, "carbs": 3.7, "fat": 0.5, "fiber": 2.8, "sugar": 0.9, "sodium": 46},
    "basil": {"description": "Basil, fresh", "calories": 23, "protein": 3.2, "carbs": 2.7, "fat": 0.6, "fiber": 1.6, "sugar": 0.3, "sodium": 4},
    "oregano": {"description": "Oregano, dried", "calories": 265, "protein": 9.0, "carbs": 68.9, "fat": 4.3, "fiber": 42.5, "sugar": 4.1, "sodium": 25},
    "thyme": {"description": "Thyme, dried", "calories": 276, "protein": 9.1, "carbs": 63.9, "fat": 7.4, "fiber": 37.0, "sugar": 1.7, "sodium": 55},
    "rosemary": {"description": "Rosemary, dried", "calories": 331, "protein": 4.9, "carbs": 64.1, "fat": 15.2, "fiber": 42.6, "sugar": 0, "sodium": 50},
    "dill": {"description": "Dill, fresh", "calories": 43, "protein": 3.5, "carbs": 7.0, "fat": 1.1, "fiber": 2.1, "sugar": 0, "sodium": 61},
    "fresh dill": {"description": "Dill, fresh", "calories": 43, "protein": 3.5, "carbs": 7.0, "fat": 1.1, "fiber": 2.1, "sugar": 0, "sodium": 61},
    "paprika": {"description": "Paprika", "calories": 282, "protein": 14.1, "carbs": 53.9, "fat": 13.0, "fiber": 34.9, "sugar": 10.3, "sodium": 68},
    "sweet paprika": {"description": "Paprika", "calories": 282, "protein": 14.1, "carbs": 53.9, "fat": 13.0, "fiber": 34.9, "sugar": 10.3, "sodium": 68},
    "cumin": {"description": "Cumin, ground", "calories": 375, "protein": 17.8, "carbs": 44.2, "fat": 22.3, "fiber": 10.5, "sugar": 2.3, "sodium": 168},
    "cinnamon": {"description": "Cinnamon, ground", "calories": 247, "protein": 4.0, "carbs": 80.6, "fat": 1.2, "fiber": 53.1, "sugar": 2.2, "sodium": 10},
    "ginger": {"description": "Ginger, ground", "calories": 335, "protein": 9.0, "carbs": 71.6, "fat": 4.2, "fiber": 14.1, "sugar": 3.4, "sodium": 27},
    "black pepper": {"description": "Pepper, black", "calories": 251, "protein": 10.4, "carbs": 63.9, "fat": 3.3, "fiber": 25.3, "sugar": 0.6, "sodium": 20},
    "pepper": {"description": "Pepper, black", "calories": 251, "protein": 10.4, "carbs": 63.9, "fat": 3.3, "fiber": 25.3, "sugar": 0.6, "sodium": 20},
    "chili powder": {"description": "Chili powder", "calories": 282, "protein": 13.5, "carbs": 49.7, "fat": 14.3, "fiber": 34.8, "sugar": 7.2, "sodium": 2867},
    "cayenne": {"description": "Cayenne pepper", "calories": 318, "protein": 12.0, "carbs": 56.6, "fat": 17.3, "fiber": 27.2, "sugar": 10.3, "sodium": 30},
    "pickle": {"description": "Pickles, dill", "calories": 11, "protein": 0.3, "carbs": 2.3, "fat": 0.2, "fiber": 1.2, "sugar": 1.1, "sodium": 1208},
    "pickled cucumber": {"description": "Pickles, dill", "calories": 11, "protein": 0.3, "carbs": 2.3, "fat": 0.2, "fiber": 1.2, "sugar": 1.1, "sodium": 1208},
    "cucumber": {"description": "Cucumber, raw", "calories": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "fiber": 0.5, "sugar": 1.7, "sodium": 2},
    "bell pepper": {"description": "Bell pepper, raw", "calories": 26, "protein": 1.0, "carbs": 6.0, "fat": 0.3, "fiber": 2.1, "sugar": 4.2, "sodium": 4},
    "mushroom": {"description": "Mushrooms, raw", "calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3, "fiber": 1.0, "sugar": 2.0, "sodium": 5},
    "mushrooms": {"description": "Mushrooms, raw", "calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3, "fiber": 1.0, "sugar": 2.0, "sodium": 5},
    "zucchini": {"description": "Zucchini, raw", "calories": 17, "protein": 1.2, "carbs": 3.1, "fat": 0.3, "fiber": 1.0, "sugar": 2.5, "sodium": 8},
    "eggplant": {"description": "Eggplant, raw", "calories": 25, "protein": 1.0, "carbs": 5.9, "fat": 0.2, "fiber": 3.0, "sugar": 3.5, "sodium": 2},
    "avocado": {"description": "Avocado, raw", "calories": 160, "protein": 2.0, "carbs": 8.5, "fat": 14.7, "fiber": 6.7, "sugar": 0.7, "sodium": 7},
    "corn": {"description": "Corn, sweet, raw", "calories": 86, "protein": 3.3, "carbs": 19.0, "fat": 1.4, "fiber": 2.7, "sugar": 6.3, "sodium": 15},
    "peas": {"description": "Peas, green, raw", "calories": 81, "protein": 5.4, "carbs": 14.5, "fat": 0.4, "fiber": 5.7, "sugar": 5.7, "sodium": 5},
    "green beans": {"description": "Green beans, raw", "calories": 31, "protein": 1.8, "carbs": 7.0, "fat": 0.1, "fiber": 2.7, "sugar": 3.3, "sodium": 6},
    "cabbage": {"description": "Cabbage, raw", "calories": 25, "protein": 1.3, "carbs": 5.8, "fat": 0.1, "fiber": 2.5, "sugar": 3.2, "sodium": 18},
    "cauliflower": {"description": "Cauliflower, raw", "calories": 25, "protein": 1.9, "carbs": 5.0, "fat": 0.3, "fiber": 2.0, "sugar": 1.9, "sodium": 30},
    "asparagus": {"description": "Asparagus, raw", "calories": 20, "protein": 2.2, "carbs": 3.9, "fat": 0.1, "fiber": 2.1, "sugar": 1.9, "sodium": 2},
    "kale": {"description": "Kale, raw", "calories": 35, "protein": 2.9, "carbs": 4.4, "fat": 1.5, "fiber": 4.1, "sugar": 0.8, "sodium": 53},
    "sweet potato": {"description": "Sweet potato, raw", "calories": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0, "sugar": 4.2, "sodium": 55},
    "gnocchi": {"description": "Gnocchi, potato", "calories": 133, "protein": 3.0, "carbs": 27.0, "fat": 1.0, "fiber": 1.5, "sugar": 0.5, "sodium": 300},
    "coconut milk": {"description": "Coconut milk, canned", "calories": 197, "protein": 2.0, "carbs": 3.3, "fat": 21.3, "fiber": 0, "sugar": 2.8, "sodium": 18},
    "coconut oil": {"description": "Oil, coconut", "calories": 892, "protein": 0, "carbs": 0, "fat": 99.1, "fiber": 0, "sugar": 0, "sodium": 0},
    "sesame oil": {"description": "Oil, sesame", "calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "sugar": 0, "sodium": 0},
    "fish sauce": {"description": "Fish sauce", "calories": 35, "protein": 5.1, "carbs": 3.6, "fat": 0, "fiber": 0, "sugar": 3.6, "sodium": 7851},
    "worcestershire sauce": {"description": "Worcestershire sauce", "calories": 78, "protein": 0, "carbs": 19.5, "fat": 0, "fiber": 0, "sugar": 10.0, "sodium": 980},
    "hot sauce": {"description": "Hot sauce", "calories": 11, "protein": 0.5, "carbs": 2.4, "fat": 0.4, "fiber": 0.5, "sugar": 1.3, "sodium": 2643},
    "teriyaki sauce": {"description": "Teriyaki sauce", "calories": 89, "protein": 5.9, "carbs": 15.6, "fat": 0, "fiber": 0.1, "sugar": 14.1, "sodium": 3833},
    "vinegar": {"description": "Vinegar, distilled", "calories": 18, "protein": 0, "carbs": 0.04, "fat": 0, "fiber": 0, "sugar": 0.04, "sodium": 2},
    "balsamic vinegar": {"description": "Vinegar, balsamic", "calories": 88, "protein": 0.5, "carbs": 17.0, "fat": 0, "fiber": 0, "sugar": 14.95, "sodium": 23},
    "red wine vinegar": {"description": "Vinegar, red wine", "calories": 19, "protein": 0, "carbs": 0.3, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 8},
    "apple cider vinegar": {"description": "Vinegar, apple cider", "calories": 21, "protein": 0, "carbs": 0.9, "fat": 0, "fiber": 0, "sugar": 0.4, "sodium": 5},
    "wine": {"description": "Wine, red", "calories": 83, "protein": 0.1, "carbs": 2.6, "fat": 0, "fiber": 0, "sugar": 0.6, "sodium": 4},
    "red wine": {"description": "Wine, red", "calories": 83, "protein": 0.1, "carbs": 2.6, "fat": 0, "fiber": 0, "sugar": 0.6, "sodium": 4},
    "white wine": {"description": "Wine, white", "calories": 82, "protein": 0.1, "carbs": 2.6, "fat": 0, "fiber": 0, "sugar": 1.0, "sodium": 5},
    "beer": {"description": "Beer", "calories": 43, "protein": 0.5, "carbs": 3.6, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 4},
    "chicken broth": {"description": "Chicken broth", "calories": 4, "protein": 0.5, "carbs": 0.3, "fat": 0.1, "fiber": 0, "sugar": 0.3, "sodium": 343},
    "beef broth": {"description": "Beef broth", "calories": 8, "protein": 1.1, "carbs": 0.1, "fat": 0.3, "fiber": 0, "sugar": 0.1, "sodium": 372},
    "vegetable broth": {"description": "Vegetable broth", "calories": 6, "protein": 0.2, "carbs": 1.1, "fat": 0.1, "fiber": 0, "sugar": 0.7, "sodium": 295},
    "stock": {"description": "Stock, chicken", "calories": 4, "protein": 0.5, "carbs": 0.3, "fat": 0.1, "fiber": 0, "sugar": 0.3, "sodium": 343},
    "tomato paste": {"description": "Tomato paste", "calories": 82, "protein": 4.3, "carbs": 18.9, "fat": 0.5, "fiber": 4.1, "sugar": 12.2, "sodium": 98},
    "tomato sauce": {"description": "Tomato sauce", "calories": 29, "protein": 1.3, "carbs": 6.3, "fat": 0.2, "fiber": 1.5, "sugar": 4.6, "sodium": 577},
    "crushed tomatoes": {"description": "Tomatoes, crushed, canned", "calories": 32, "protein": 1.6, "carbs": 7.3, "fat": 0.3, "fiber": 1.9, "sugar": 4.0, "sodium": 132},
    "diced tomatoes": {"description": "Tomatoes, diced, canned", "calories": 17, "protein": 0.8, "carbs": 4.0, "fat": 0.1, "fiber": 0.9, "sugar": 2.5, "sodium": 143},
    "coconut": {"description": "Coconut, shredded", "calories": 660, "protein": 6.9, "carbs": 23.7, "fat": 64.5, "fiber": 16.3, "sugar": 7.4, "sodium": 37},
    "peanut butter": {"description": "Peanut butter", "calories": 588, "protein": 25.1, "carbs": 19.6, "fat": 50.4, "fiber": 6.0, "sugar": 9.2, "sodium": 426},
    "almond butter": {"description": "Almond butter", "calories": 614, "protein": 21.0, "carbs": 18.8, "fat": 55.5, "fiber": 10.3, "sugar": 4.4, "sodium": 7},
    "jam": {"description": "Jam/preserves", "calories": 278, "protein": 0.4, "carbs": 68.9, "fat": 0.1, "fiber": 1.1, "sugar": 48.5, "sodium": 32},
    "jelly": {"description": "Jelly", "calories": 267, "protein": 0.1, "carbs": 69.8, "fat": 0, "fiber": 0.3, "sugar": 54.3, "sodium": 25},
    "oats": {"description": "Oats, rolled", "calories": 379, "protein": 13.2, "carbs": 67.7, "fat": 6.5, "fiber": 10.1, "sugar": 0, "sodium": 6},
    "oatmeal": {"description": "Oatmeal, cooked", "calories": 68, "protein": 2.4, "carbs": 12.0, "fat": 1.4, "fiber": 1.7, "sugar": 0.5, "sodium": 49},
    "cornstarch": {"description": "Cornstarch", "calories": 381, "protein": 0.3, "carbs": 91.3, "fat": 0.1, "fiber": 0.9, "sugar": 0, "sodium": 9},
    "cornmeal": {"description": "Cornmeal", "calories": 370, "protein": 8.1, "carbs": 79.0, "fat": 3.6, "fiber": 7.3, "sugar": 0.6, "sodium": 7},
    "tortilla": {"description": "Tortilla, flour", "calories": 312, "protein": 8.3, "carbs": 51.0, "fat": 8.0, "fiber": 3.5, "sugar": 3.0, "sodium": 617},
    "tortillas": {"description": "Tortilla, flour", "calories": 312, "protein": 8.3, "carbs": 51.0, "fat": 8.0, "fiber": 3.5, "sugar": 3.0, "sodium": 617},
    "noodles": {"description": "Noodles, egg", "calories": 138, "protein": 4.5, "carbs": 25.0, "fat": 2.1, "fiber": 1.2, "sugar": 0.3, "sodium": 5},
    "ramen": {"description": "Ramen noodles", "calories": 436, "protein": 10.0, "carbs": 62.0, "fat": 17.0, "fiber": 2.0, "sugar": 1.0, "sodium": 1820},
    "spaghetti": {"description": "Spaghetti, cooked", "calories": 131, "protein": 5.0, "carbs": 25.0, "fat": 1.1, "fiber": 1.8, "sugar": 0.6, "sodium": 1},
}

def search_local_db(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a food item in the local common foods database.
    Returns match or None if not found.
    """
    query_lower = query.lower().strip()
    
    if query_lower in COMMON_FOODS_DB:
        food = COMMON_FOODS_DB[query_lower]
        return {
            "fdc_id": None,
            "description": food["description"],
            "serving_size": 100,
            "serving_unit": "g",
            "nutrients_per_100g": {
                "calories": {"value": food["calories"], "unit": "kcal"},
                "protein": {"value": food["protein"], "unit": "g"},
                "carbs": {"value": food["carbs"], "unit": "g"},
                "fat": {"value": food["fat"], "unit": "g"},
                "fiber": {"value": food["fiber"], "unit": "g"},
                "sugar": {"value": food["sugar"], "unit": "g"},
                "sodium": {"value": food["sodium"], "unit": "mg"},
            },
            "source": "local"
        }
    
    for key, food in COMMON_FOODS_DB.items():
        if key in query_lower or query_lower in key:
            return {
                "fdc_id": None,
                "description": food["description"],
                "serving_size": 100,
                "serving_unit": "g",
                "nutrients_per_100g": {
                    "calories": {"value": food["calories"], "unit": "kcal"},
                    "protein": {"value": food["protein"], "unit": "g"},
                    "carbs": {"value": food["carbs"], "unit": "g"},
                    "fat": {"value": food["fat"], "unit": "g"},
                    "fiber": {"value": food["fiber"], "unit": "g"},
                    "sugar": {"value": food["sugar"], "unit": "g"},
                    "sodium": {"value": food["sodium"], "unit": "mg"},
                },
                "source": "local"
            }
    
    return None

def search_food(query: str) -> Optional[Dict[str, Any]]:
    """
    Search for a food item. Tries local database first, then USDA API.
    Returns the best match or None if not found.
    """
    cache_key = query.lower().strip()
    if cache_key in nutrition_cache:
        logger.debug(f"Cache hit for: {query}")
        return nutrition_cache[cache_key]
    
    local_result = search_local_db(query)
    if local_result:
        nutrition_cache[cache_key] = local_result
        logger.info(f"Local DB match for '{query}': {local_result['description']}")
        return local_result
    
    try:
        url = f"{USDA_API_BASE}/foods/search"
        params = {
            "api_key": USDA_API_KEY,
            "query": query,
            "pageSize": 5,
            "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("error"):
            logger.warning(f"USDA API error: {data.get('error')}")
            return None
        
        foods = data.get("foods", [])
        
        if not foods:
            logger.warning(f"No USDA results for: {query}")
            return None
        
        best_match = foods[0]
        
        nutrients = {}
        for nutrient in best_match.get("foodNutrients", []):
            nutrient_id = nutrient.get("nutrientId")
            for name, nid in NUTRIENT_IDS.items():
                if nutrient_id == nid:
                    nutrients[name] = {
                        "value": nutrient.get("value", 0),
                        "unit": nutrient.get("unitName", ""),
                    }
        
        result = {
            "fdc_id": best_match.get("fdcId"),
            "description": best_match.get("description"),
            "serving_size": best_match.get("servingSize", 100),
            "serving_unit": best_match.get("servingSizeUnit", "g"),
            "nutrients_per_100g": nutrients,
        }
        
        nutrition_cache[cache_key] = result
        logger.info(f"USDA match for '{query}': {result['description']}")
        return result
        
    except requests.RequestException as e:
        logger.error(f"USDA API error for '{query}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error searching food '{query}': {e}")
        return None

SMALL_AMOUNT_INGREDIENTS = {
    "salt", "pepper", "black pepper", "white pepper", "paprika", "sweet paprika",
    "cumin", "cinnamon", "oregano", "thyme", "rosemary", "basil", "parsley",
    "cilantro", "dill", "fresh dill", "chili powder", "cayenne", "nutmeg",
    "garlic powder", "onion powder", "ginger", "turmeric", "curry powder",
}

def estimate_grams(quantity: Optional[float], unit: Optional[str], ingredient_name: str) -> float:
    """
    Estimate weight in grams based on quantity and unit.
    Returns estimated grams.
    """
    ingredient_lower = ingredient_name.lower().strip()
    unit_lower = (unit or "").lower().strip()
    
    if unit_lower in ("to taste", "as needed", "for garnish", "optional"):
        if any(small in ingredient_lower for small in SMALL_AMOUNT_INGREDIENTS):
            return 2.0
        return 10.0
    
    if quantity is None or quantity <= 0:
        if any(small in ingredient_lower for small in SMALL_AMOUNT_INGREDIENTS):
            return 2.0
        return 50.0
    
    if unit is None or unit.strip() == "":
        return quantity * 100.0
    
    if unit_lower in UNIT_CONVERSIONS_TO_GRAMS:
        return quantity * UNIT_CONVERSIONS_TO_GRAMS[unit_lower]
    
    return quantity * 100.0

def get_ingredient_nutrition(ingredient_name: str, quantity: Optional[float], unit: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Get nutrition information for an ingredient.
    Returns scaled nutrition based on quantity and unit.
    """
    clean_name = re.sub(r'\([^)]*\)', '', ingredient_name).strip()
    clean_name = re.sub(r',.*$', '', clean_name).strip()
    
    food_data = search_food(clean_name)
    if not food_data:
        return None
    
    grams = estimate_grams(quantity, unit, clean_name)
    scale = grams / 100.0
    
    nutrients = food_data.get("nutrients_per_100g", {})
    scaled_nutrients = {}
    
    for name, data in nutrients.items():
        scaled_nutrients[name] = round(data["value"] * scale, 2)
    
    return {
        "ingredient": ingredient_name,
        "matched_food": food_data["description"],
        "estimated_grams": round(grams, 1),
        "nutrients": scaled_nutrients,
    }

def calculate_recipe_nutrition(ingredients: List[Dict[str, Any]], servings: int = 1) -> Dict[str, Any]:
    """
    Calculate total nutrition for a recipe based on its ingredients.
    
    Args:
        ingredients: List of ingredient dicts with 'name', 'quantity', 'unit'
        servings: Number of servings the recipe makes
    
    Returns:
        Dict with total and per-serving nutrition, plus ingredient breakdown
    """
    totals = {
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
        "fiber": 0,
        "sugar": 0,
        "sodium": 0,
    }
    
    ingredient_breakdown = []
    missing_ingredients = []
    
    for ing in ingredients:
        name = ing.get("name") or ing.get("ingredient", {}).get("name", "")
        quantity = ing.get("quantity")
        unit = ing.get("unit")
        
        if not name:
            continue
        
        nutrition = get_ingredient_nutrition(name, quantity, unit)
        
        if nutrition:
            ingredient_breakdown.append(nutrition)
            for nutrient, value in nutrition["nutrients"].items():
                if nutrient in totals:
                    totals[nutrient] += value
        else:
            missing_ingredients.append(name)
    
    for key in totals:
        totals[key] = round(totals[key], 1)
    
    servings = max(1, servings)
    per_serving = {key: round(value / servings, 1) for key, value in totals.items()}
    
    return {
        "total": totals,
        "per_serving": per_serving,
        "servings": servings,
        "ingredients_analyzed": len(ingredient_breakdown),
        "ingredients_missing": missing_ingredients,
        "breakdown": ingredient_breakdown,
    }

def parse_servings(servings_str: Optional[str]) -> int:
    """
    Parse servings string like '4', '4-6', '4 servings' into an integer.
    Returns the first/lower number found, defaulting to 1.
    """
    if not servings_str:
        return 1
    
    match = re.search(r'(\d+)', str(servings_str))
    if match:
        return int(match.group(1))
    return 1
