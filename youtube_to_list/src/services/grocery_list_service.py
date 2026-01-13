import logging
import re
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime

from src.models import GroceryList, GroceryListItem, Recipe

logger = logging.getLogger(__name__)

REDUNDANT_PREFIXES = [
    "canned", "fresh", "frozen", "dried", "chopped", "diced", "minced",
    "sliced", "shredded", "grated", "crushed", "ground", "whole", "raw",
    "cooked", "roasted", "grilled", "baked", "fried", "steamed", "boiled",
    "organic", "natural", "pure", "plain", "unsalted", "salted", "unsweetened",
    "sweetened", "light", "low-fat", "fat-free", "reduced-fat", "full-fat",
    "boneless", "skinless", "bone-in", "skin-on", "lean", "extra-lean",
    "thick-cut", "thin-sliced", "large", "medium", "small", "extra-large",
    "warm", "cold", "hot", "room temperature", "melted", "softened",
]

PANTRY_STAPLES = [
    "salt", "pepper", "black pepper", "white pepper", "sugar", "flour",
    "olive oil", "vegetable oil", "cooking oil", "butter", "garlic",
    "onion powder", "garlic powder", "paprika", "cumin", "oregano",
    "basil", "thyme", "rosemary", "cinnamon", "nutmeg", "bay leaf",
    "red pepper flake", "cayenne", "chili powder", "curry powder",
    "italian seasoning", "vanilla extract", "vanilla", "baking powder",
    "baking soda", "cornstarch", "soy sauce", "vinegar", "honey",
    "breadcrumb", "breadcrumbs", "panko",
]

UNIT_TO_ML = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "cup": 236.588,
    "cups": 236.588,
    "tbsp": 14.787,
    "tablespoon": 14.787,
    "tablespoons": 14.787,
    "tsp": 4.929,
    "teaspoon": 4.929,
    "teaspoons": 4.929,
    "fl oz": 29.574,
    "fluid ounce": 29.574,
    "pint": 473.176,
    "pints": 473.176,
    "quart": 946.353,
    "quarts": 946.353,
    "gallon": 3785.41,
    "gallons": 3785.41,
}

UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "oz": 28.3495,
    "ounce": 28.3495,
    "ounces": 28.3495,
    "lb": 453.592,
    "lbs": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
}

# US Retail Package Sizes for common grocery items
# Used to round ingredient quantities to practical shopping units
US_RETAIL_PACKAGES = {
    "milk": {
        "type": "volume",
        "packages": [
            {"size_ml": 473, "label": "1 pint"},
            {"size_ml": 946, "label": "1 quart"},
            {"size_ml": 1893, "label": "1/2 gallon"},
            {"size_ml": 3785, "label": "1 gallon"},
        ],
    },
    "cream": {
        "type": "volume",
        "packages": [
            {"size_ml": 236, "label": "8 oz"},
            {"size_ml": 473, "label": "1 pint"},
            {"size_ml": 946, "label": "1 quart"},
        ],
    },
    "half and half": {
        "type": "volume",
        "packages": [
            {"size_ml": 473, "label": "1 pint"},
            {"size_ml": 946, "label": "1 quart"},
        ],
    },
    "buttermilk": {
        "type": "volume",
        "packages": [
            {"size_ml": 946, "label": "1 quart"},
            {"size_ml": 1893, "label": "1/2 gallon"},
        ],
    },
    "butter": {
        "type": "weight",
        "packages": [
            {"size_g": 113, "label": "1 stick"},
            {"size_g": 227, "label": "2 sticks"},
            {"size_g": 454, "label": "1 lb"},
        ],
    },
    "egg": {
        "type": "count",
        "packages": [
            {"count": 6, "label": "half dozen"},
            {"count": 12, "label": "1 dozen"},
            {"count": 18, "label": "18-count"},
        ],
    },
    "eggs": {
        "type": "count",
        "packages": [
            {"count": 6, "label": "half dozen"},
            {"count": 12, "label": "1 dozen"},
            {"count": 18, "label": "18-count"},
        ],
    },
    "sour cream": {
        "type": "volume",
        "packages": [
            {"size_ml": 236, "label": "8 oz"},
            {"size_ml": 473, "label": "16 oz"},
        ],
    },
    "yogurt": {
        "type": "volume",
        "packages": [
            {"size_ml": 170, "label": "6 oz"},
            {"size_ml": 473, "label": "16 oz"},
            {"size_ml": 907, "label": "32 oz"},
        ],
    },
    "chicken broth": {
        "type": "volume",
        "packages": [
            {"size_ml": 414, "label": "14 oz can"},
            {"size_ml": 946, "label": "32 oz carton"},
        ],
    },
    "beef broth": {
        "type": "volume",
        "packages": [
            {"size_ml": 414, "label": "14 oz can"},
            {"size_ml": 946, "label": "32 oz carton"},
        ],
    },
    "vegetable broth": {
        "type": "volume",
        "packages": [
            {"size_ml": 414, "label": "14 oz can"},
            {"size_ml": 946, "label": "32 oz carton"},
        ],
    },
    "olive oil": {
        "type": "volume",
        "packages": [
            {"size_ml": 500, "label": "17 oz bottle"},
            {"size_ml": 750, "label": "25 oz bottle"},
            {"size_ml": 1000, "label": "34 oz bottle"},
        ],
    },
    "vegetable oil": {
        "type": "volume",
        "packages": [
            {"size_ml": 710, "label": "24 oz bottle"},
            {"size_ml": 1420, "label": "48 oz bottle"},
        ],
    },
}

# TODO: Future locale support for international markets
# MARKET_RETAIL_PACKAGES = {
#     "US": US_RETAIL_PACKAGES,
#     "UK": {
#         "milk": {"type": "volume", "packages": [
#             {"size_ml": 568, "label": "1 pint"},      # UK pint = 568ml
#             {"size_ml": 1136, "label": "2 pints"},
#             {"size_ml": 2272, "label": "4 pints"},
#         ]},
#         # UK uses metric for most items, imperial for milk/beer
#     },
#     "EU": {
#         "milk": {"type": "volume", "packages": [
#             {"size_ml": 500, "label": "500 ml"},
#             {"size_ml": 1000, "label": "1 L"},
#             {"size_ml": 2000, "label": "2 L"},
#         ]},
#         # EU uses metric system throughout
#     },
# }
# DEFAULT_MARKET = "US"

CATEGORY_KEYWORDS = {
    "Produce": [
        "lettuce", "tomato", "onion", "garlic", "pepper", "carrot", "celery",
        "broccoli", "spinach", "kale", "cucumber", "zucchini", "squash",
        "potato", "sweet potato", "mushroom", "avocado", "lemon", "lime",
        "orange", "apple", "banana", "berry", "strawberry", "blueberry",
        "grape", "mango", "pineapple", "melon", "watermelon", "peach",
        "pear", "plum", "cherry", "ginger", "cilantro", "parsley", "basil",
        "mint", "dill", "rosemary", "thyme", "scallion", "leek", "shallot",
        "cabbage", "corn", "peas", "beans", "asparagus", "artichoke",
        "eggplant", "beet", "radish", "turnip", "spring onion", "green onion",
    ],
    "Dairy": [
        "milk", "cream", "butter", "cheese", "yogurt", "sour cream",
        "cream cheese", "cottage cheese", "ricotta", "mozzarella",
        "parmesan", "cheddar", "feta", "goat cheese", "brie", "swiss",
        "half and half", "whipping cream", "heavy cream", "buttermilk",
    ],
    "Meat & Seafood": [
        "chicken", "beef", "pork", "lamb", "turkey", "duck", "veal",
        "bacon", "ham", "sausage", "ground beef", "steak", "roast",
        "salmon", "tuna", "shrimp", "crab", "lobster", "fish", "cod",
        "tilapia", "halibut", "scallop", "mussel", "clam", "oyster",
        "anchovy", "sardine", "trout", "sea bass", "prawn",
    ],
    "Bakery & Bread": [
        "bread", "baguette", "roll", "bun", "croissant", "bagel",
        "tortilla", "pita", "naan", "flatbread", "english muffin",
        "breadcrumb", "panko", "crouton",
    ],
    "Pantry": [
        "flour", "sugar", "salt", "pepper", "oil", "olive oil", "vegetable oil",
        "vinegar", "soy sauce", "honey", "maple syrup", "vanilla",
        "baking powder", "baking soda", "yeast", "cornstarch", "cocoa",
        "chocolate", "rice", "pasta", "noodle", "oat", "cereal",
        "canned", "broth", "stock", "tomato paste", "tomato sauce",
        "beans", "lentil", "chickpea", "peanut butter", "jam", "jelly",
        "mustard", "ketchup", "mayonnaise", "hot sauce", "worcestershire",
        "sesame oil", "fish sauce", "oyster sauce", "hoisin", "sriracha",
        "cumin", "paprika", "cinnamon", "oregano", "basil", "thyme",
        "nutmeg", "clove", "cardamom", "turmeric", "curry", "chili",
        "bay leaf", "red pepper flake", "cayenne", "garlic powder",
        "onion powder", "italian seasoning", "taco seasoning",
    ],
    "Frozen": [
        "frozen", "ice cream", "frozen vegetable", "frozen fruit",
        "frozen pizza", "frozen meal",
    ],
    "Beverages": [
        "water", "juice", "soda", "coffee", "tea", "wine", "beer",
        "sparkling", "coconut water", "almond milk", "oat milk", "soy milk",
    ],
    "Eggs": [
        "egg", "eggs",
    ],
}


def categorize_ingredient(ingredient_name: str) -> str:
    """Determine the grocery category for an ingredient."""
    name_lower = ingredient_name.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    
    return "Other"


def clean_ingredient_name(name: str, unit: Optional[str] = None) -> str:
    """
    Clean ingredient name by removing redundant prefixes.
    E.g., "Canned Tuna" with unit "can" -> "Tuna"
    """
    cleaned = name.strip()
    name_lower = cleaned.lower()
    
    unit_related_words = []
    if unit:
        unit_lower = unit.lower()
        if "can" in unit_lower:
            unit_related_words.extend(["canned", "cans"])
        if "frozen" in unit_lower:
            unit_related_words.append("frozen")
    
    words_to_remove = REDUNDANT_PREFIXES + unit_related_words
    
    for prefix in words_to_remove:
        pattern = rf'^\s*{re.escape(prefix)}\s+'
        if re.match(pattern, name_lower, re.IGNORECASE):
            cleaned = re.sub(pattern, '', cleaned, count=1, flags=re.IGNORECASE).strip()
            name_lower = cleaned.lower()
    
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    
    return cleaned


def is_pantry_staple(ingredient_name: str) -> bool:
    """Check if an ingredient is a common pantry staple."""
    name_lower = ingredient_name.lower()
    return any(staple in name_lower for staple in PANTRY_STAPLES)


def is_to_taste_item(quantity: Optional[float], unit: Optional[str], ingredient_name: str) -> bool:
    """Determine if an item is a 'to taste' ingredient that shouldn't show quantity."""
    if quantity is None or quantity == 0:
        return True
    
    if is_pantry_staple(ingredient_name):
        unit_lower = (unit or "").lower()
        if unit_lower in ["tsp", "teaspoon", "teaspoons", "tbsp", "tablespoon", "tablespoons", "pinch", "dash"]:
            if quantity <= 2:
                return True
    
    return False


def normalize_unit(unit: Optional[str]) -> Optional[str]:
    """Normalize unit to a standard form."""
    if not unit:
        return None
    
    unit_lower = unit.lower().strip()
    
    unit_mappings = {
        "tablespoon": "tbsp",
        "tablespoons": "tbsp",
        "teaspoon": "tsp",
        "teaspoons": "tsp",
        "cups": "cup",
        "ounces": "oz",
        "ounce": "oz",
        "pounds": "lb",
        "pound": "lb",
        "grams": "g",
        "gram": "g",
        "kilograms": "kg",
        "kilogram": "kg",
        "liters": "l",
        "liter": "l",
        "milliliters": "ml",
        "milliliter": "ml",
    }
    
    return unit_mappings.get(unit_lower, unit_lower)


def can_combine_units(unit1: Optional[str], unit2: Optional[str]) -> bool:
    """Check if two units can be combined (same type: volume or weight)."""
    if unit1 is None and unit2 is None:
        return True
    if unit1 is None or unit2 is None:
        return False
    
    u1 = normalize_unit(unit1)
    u2 = normalize_unit(unit2)
    
    if u1 == u2:
        return True
    
    both_volume = u1 in UNIT_TO_ML and u2 in UNIT_TO_ML
    both_weight = u1 in UNIT_TO_GRAMS and u2 in UNIT_TO_GRAMS
    
    return both_volume or both_weight


def convert_and_add(qty1: float, unit1: Optional[str], qty2: float, unit2: Optional[str], ingredient_name: str = "") -> tuple:
    """Convert units and add quantities. Returns (total_qty, result_unit)."""
    u1 = normalize_unit(unit1)
    u2 = normalize_unit(unit2)
    
    if u1 == u2:
        return (qty1 + qty2, u1)
    
    if u1 in UNIT_TO_ML and u2 in UNIT_TO_ML:
        total_ml = qty1 * UNIT_TO_ML[u1] + qty2 * UNIT_TO_ML[u2]
        return convert_ml_to_practical_unit(total_ml, ingredient_name)
    
    if u1 in UNIT_TO_GRAMS and u2 in UNIT_TO_GRAMS:
        total_g = qty1 * UNIT_TO_GRAMS[u1] + qty2 * UNIT_TO_GRAMS[u2]
        if total_g >= 453.592:
            return (round(total_g / 453.592, 2), "lb")
        elif total_g >= 28.3495:
            return (round(total_g / 28.3495, 2), "oz")
        else:
            return (round(total_g, 1), "g")
    
    return (qty1 + qty2, u1 or u2)


def convert_ml_to_practical_unit(total_ml: float, ingredient_name: str = "") -> tuple:
    """Convert milliliters to a practical grocery shopping unit."""
    name_lower = ingredient_name.lower()
    is_dairy_liquid = any(d in name_lower for d in ["milk", "cream", "half and half", "buttermilk"])
    
    if total_ml >= 946.353:
        qty = total_ml / 946.353
        if qty >= 3.5:
            return (round(qty / 4, 2), "gallon")
        return (round(qty, 2), "quart")
    elif total_ml >= 473.176:
        return (round(total_ml / 473.176, 2), "pint")
    elif total_ml >= 236.588 or is_dairy_liquid:
        cups = total_ml / 236.588
        if cups < 0.25:
            return (0.25, "cup")
        return (round(cups, 2), "cup")
    elif total_ml >= 14.787:
        return (round(total_ml / 14.787, 2), "tbsp")
    else:
        return (round(total_ml / 4.929, 2), "tsp")


def find_retail_package_match(ingredient_name: str) -> Optional[Dict]:
    """Find matching retail package definition for an ingredient."""
    name_lower = ingredient_name.lower()
    
    for package_key, package_def in US_RETAIL_PACKAGES.items():
        if package_key in name_lower:
            return {"key": package_key, **package_def}
    
    return None


def format_exact_amount(quantity: float, unit: str) -> str:
    """Format a quantity and unit as a readable string."""
    if quantity is None:
        return ""
    
    if quantity == int(quantity):
        qty_str = str(int(quantity))
    elif quantity < 1:
        fractions = {0.25: "1/4", 0.33: "1/3", 0.5: "1/2", 0.67: "2/3", 0.75: "3/4"}
        for frac_val, frac_str in fractions.items():
            if abs(quantity - frac_val) < 0.05:
                qty_str = frac_str
                break
        else:
            qty_str = f"{quantity:.2f}".rstrip('0').rstrip('.')
    else:
        qty_str = f"{quantity:.2f}".rstrip('0').rstrip('.')
    
    return f"{qty_str} {unit}" if unit else qty_str


def round_to_retail_package(
    ingredient_name: str,
    quantity: Optional[float],
    unit: Optional[str]
) -> Dict[str, Any]:
    """
    Round ingredient quantity to the nearest US retail package size.
    Returns dict with retail_package, retail_package_count, and exact_amount.
    """
    result = {
        "retail_package": None,
        "retail_package_count": None,
        "exact_amount": None,
    }
    
    if quantity is None or unit is None:
        return result
    
    package_def = find_retail_package_match(ingredient_name)
    if not package_def:
        result["exact_amount"] = format_exact_amount(quantity, unit)
        return result
    
    package_type = package_def["type"]
    packages = package_def["packages"]
    
    if package_type == "volume":
        normalized_unit = normalize_unit(unit)
        if normalized_unit not in UNIT_TO_ML:
            result["exact_amount"] = format_exact_amount(quantity, unit)
            return result
        
        total_ml = quantity * UNIT_TO_ML[normalized_unit]
        exact_cups = total_ml / 236.588
        result["exact_amount"] = format_exact_amount(round(exact_cups, 2), "cup")
        
        for pkg in packages:
            if pkg["size_ml"] >= total_ml:
                result["retail_package"] = pkg["label"]
                result["retail_package_count"] = 1
                return result
        
        largest = packages[-1]
        count = int((total_ml / largest["size_ml"]) + 0.99)
        result["retail_package"] = largest["label"]
        result["retail_package_count"] = count
        
    elif package_type == "weight":
        normalized_unit = normalize_unit(unit)
        if normalized_unit not in UNIT_TO_GRAMS:
            if normalized_unit in ["tbsp", "tsp", "cup"]:
                if "butter" in ingredient_name.lower():
                    if normalized_unit == "tbsp":
                        total_g = quantity * 14.2
                    elif normalized_unit == "cup":
                        total_g = quantity * 227
                    else:
                        result["exact_amount"] = format_exact_amount(quantity, unit)
                        return result
                else:
                    result["exact_amount"] = format_exact_amount(quantity, unit)
                    return result
            else:
                result["exact_amount"] = format_exact_amount(quantity, unit)
                return result
        else:
            total_g = quantity * UNIT_TO_GRAMS[normalized_unit]
        
        if "butter" in ingredient_name.lower():
            tbsp_equivalent = total_g / 14.2
            result["exact_amount"] = format_exact_amount(round(tbsp_equivalent, 1), "tbsp")
        else:
            result["exact_amount"] = format_exact_amount(round(total_g / 28.35, 1), "oz")
        
        for pkg in packages:
            if pkg["size_g"] >= total_g:
                result["retail_package"] = pkg["label"]
                result["retail_package_count"] = 1
                return result
        
        largest = packages[-1]
        count = int((total_g / largest["size_g"]) + 0.99)
        result["retail_package"] = largest["label"]
        result["retail_package_count"] = count
        
    elif package_type == "count":
        try:
            count_needed = int(quantity)
        except (ValueError, TypeError):
            count_needed = 1
        
        result["exact_amount"] = f"{count_needed} needed"
        
        for pkg in packages:
            if pkg["count"] >= count_needed:
                result["retail_package"] = pkg["label"]
                result["retail_package_count"] = 1
                return result
        
        largest = packages[-1]
        count = int((count_needed / largest["count"]) + 0.99)
        result["retail_package"] = largest["label"]
        result["retail_package_count"] = count
    
    return result


def consolidate_ingredients(recipes: List[Recipe]) -> List[Dict[str, Any]]:
    """
    Consolidate ingredients from multiple recipes.
    Combines same ingredients and converts compatible units.
    Cleans ingredient names and handles 'to taste' items.
    Adds retail package sizing for US market.
    """
    consolidated: Dict[str, Dict[str, Any]] = {}
    
    for recipe in recipes:
        for ri in recipe.ingredients:
            unit = normalize_unit(ri.unit)
            cleaned_name = clean_ingredient_name(ri.ingredient.name, unit)
            key = cleaned_name.lower().strip()
            
            if key not in consolidated:
                if is_to_taste_item(ri.quantity, ri.unit, ri.ingredient.name):
                    quantity = None
                    display_unit = None
                else:
                    quantity = ri.quantity
                    display_unit = unit
                
                consolidated[key] = {
                    "ingredient_name": cleaned_name,
                    "quantity": quantity,
                    "unit": display_unit,
                    "category": categorize_ingredient(ri.ingredient.name),
                    "recipe_ids": [recipe.id],
                }
            else:
                existing = consolidated[key]
                existing["recipe_ids"].append(recipe.id)
                
                if is_to_taste_item(ri.quantity, ri.unit, ri.ingredient.name):
                    continue
                
                if existing["quantity"] is None and ri.quantity is None:
                    continue
                
                if existing["quantity"] is None:
                    existing["quantity"] = ri.quantity
                    existing["unit"] = unit
                elif ri.quantity is not None:
                    if can_combine_units(existing["unit"], ri.unit):
                        new_qty, new_unit = convert_and_add(
                            existing["quantity"], existing["unit"],
                            ri.quantity, ri.unit,
                            cleaned_name
                        )
                        existing["quantity"] = new_qty
                        existing["unit"] = new_unit
                    else:
                        existing["quantity"] = existing["quantity"] + ri.quantity
    
    result = []
    for item_data in consolidated.values():
        retail_info = round_to_retail_package(
            item_data["ingredient_name"],
            item_data["quantity"],
            item_data["unit"]
        )
        item_data["retail_package"] = retail_info["retail_package"]
        item_data["retail_package_count"] = retail_info["retail_package_count"]
        item_data["exact_amount"] = retail_info["exact_amount"]
        result.append(item_data)
    
    return result


def create_grocery_list(db: Session, name: str, recipe_ids: List[int]) -> GroceryList:
    """Create a new grocery list from recipe IDs."""
    recipes = db.query(Recipe).filter(
        Recipe.id.in_(recipe_ids),
        Recipe.is_deleted == False
    ).all()
    
    if not recipes:
        raise ValueError("No valid recipes found")
    
    grocery_list = GroceryList(name=name)
    grocery_list.recipes = recipes
    
    consolidated = consolidate_ingredients(recipes)
    
    for item_data in consolidated:
        item = GroceryListItem(
            ingredient_name=item_data["ingredient_name"],
            quantity=item_data["quantity"],
            unit=item_data["unit"],
            category=item_data["category"],
            recipe_ids=item_data["recipe_ids"],
            retail_package=item_data.get("retail_package"),
            retail_package_count=item_data.get("retail_package_count"),
            exact_amount=item_data.get("exact_amount"),
            is_checked=False,
        )
        grocery_list.items.append(item)
    
    db.add(grocery_list)
    db.commit()
    db.refresh(grocery_list)
    
    logger.info(f"Created grocery list '{name}' with {len(grocery_list.items)} items from {len(recipes)} recipes")
    return grocery_list


def get_grocery_list(db: Session, list_id: int) -> Optional[GroceryList]:
    """Get a grocery list by ID."""
    return db.query(GroceryList).filter(GroceryList.id == list_id).first()


def get_all_grocery_lists(db: Session) -> List[GroceryList]:
    """Get all grocery lists."""
    return db.query(GroceryList).order_by(GroceryList.updated_at.desc()).all()


def add_recipe_to_list(db: Session, list_id: int, recipe_id: int) -> Optional[GroceryList]:
    """Add a recipe to an existing grocery list."""
    grocery_list = db.query(GroceryList).filter(GroceryList.id == list_id).first()
    if not grocery_list:
        return None
    
    recipe = db.query(Recipe).filter(
        Recipe.id == recipe_id,
        Recipe.is_deleted == False
    ).first()
    if not recipe:
        return None
    
    if recipe in grocery_list.recipes:
        return grocery_list
    
    grocery_list.recipes.append(recipe)
    
    for ri in recipe.ingredients:
        unit = normalize_unit(ri.unit)
        cleaned_name = clean_ingredient_name(ri.ingredient.name, unit)
        cleaned_name_lower = cleaned_name.lower().strip()
        
        existing_item = None
        for item in grocery_list.items:
            if item.ingredient_name.lower().strip() == cleaned_name_lower:
                existing_item = item
                break
        
        if is_to_taste_item(ri.quantity, ri.unit, ri.ingredient.name):
            if existing_item:
                if existing_item.recipe_ids is None:
                    existing_item.recipe_ids = []
                if recipe_id not in existing_item.recipe_ids:
                    existing_item.recipe_ids = existing_item.recipe_ids + [recipe_id]
            else:
                new_item = GroceryListItem(
                    ingredient_name=cleaned_name,
                    quantity=None,
                    unit=None,
                    category=categorize_ingredient(ri.ingredient.name),
                    recipe_ids=[recipe_id],
                    is_checked=False,
                )
                grocery_list.items.append(new_item)
            continue
        
        if existing_item:
            if existing_item.recipe_ids is None:
                existing_item.recipe_ids = []
            if recipe_id not in existing_item.recipe_ids:
                existing_item.recipe_ids = existing_item.recipe_ids + [recipe_id]
            
            if ri.quantity and existing_item.quantity:
                if can_combine_units(existing_item.unit, ri.unit):
                    new_qty, new_unit = convert_and_add(
                        existing_item.quantity, existing_item.unit,
                        ri.quantity, ri.unit,
                        cleaned_name
                    )
                    existing_item.quantity = new_qty
                    existing_item.unit = new_unit
                else:
                    existing_item.quantity = existing_item.quantity + ri.quantity
            elif ri.quantity and not existing_item.quantity:
                existing_item.quantity = ri.quantity
                existing_item.unit = unit
            
            retail_info = round_to_retail_package(
                existing_item.ingredient_name,
                existing_item.quantity,
                existing_item.unit
            )
            existing_item.retail_package = retail_info["retail_package"]
            existing_item.retail_package_count = retail_info["retail_package_count"]
            existing_item.exact_amount = retail_info["exact_amount"]
        else:
            retail_info = round_to_retail_package(cleaned_name, ri.quantity, unit)
            new_item = GroceryListItem(
                ingredient_name=cleaned_name,
                quantity=ri.quantity,
                unit=unit,
                category=categorize_ingredient(ri.ingredient.name),
                recipe_ids=[recipe_id],
                retail_package=retail_info["retail_package"],
                retail_package_count=retail_info["retail_package_count"],
                exact_amount=retail_info["exact_amount"],
                is_checked=False,
            )
            grocery_list.items.append(new_item)
    
    grocery_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(grocery_list)
    
    logger.info(f"Added recipe {recipe_id} to grocery list {list_id}")
    return grocery_list


def remove_recipe_from_list(db: Session, list_id: int, recipe_id: int) -> Optional[GroceryList]:
    """Remove a recipe from a grocery list and update items."""
    grocery_list = db.query(GroceryList).filter(GroceryList.id == list_id).first()
    if not grocery_list:
        return None
    
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if recipe and recipe in grocery_list.recipes:
        grocery_list.recipes.remove(recipe)
    
    items_to_remove = []
    for item in grocery_list.items:
        if item.recipe_ids and recipe_id in item.recipe_ids:
            item.recipe_ids = [rid for rid in item.recipe_ids if rid != recipe_id]
            if not item.recipe_ids:
                items_to_remove.append(item)
    
    for item in items_to_remove:
        db.delete(item)
    
    grocery_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(grocery_list)
    
    return grocery_list


def toggle_item(db: Session, item_id: int) -> Optional[GroceryListItem]:
    """Toggle the checked state of a grocery list item."""
    item = db.query(GroceryListItem).filter(GroceryListItem.id == item_id).first()
    if not item:
        return None
    
    item.is_checked = not item.is_checked
    item.grocery_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    
    return item


def update_item(db: Session, item_id: int, update_data: dict) -> Optional[GroceryListItem]:
    """Update a grocery list item."""
    item = db.query(GroceryListItem).filter(GroceryListItem.id == item_id).first()
    if not item:
        return None
    
    for field, value in update_data.items():
        if hasattr(item, field) and value is not None:
            setattr(item, field, value)
    
    item.grocery_list.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    
    return item


def delete_grocery_list(db: Session, list_id: int) -> bool:
    """Delete a grocery list."""
    grocery_list = db.query(GroceryList).filter(GroceryList.id == list_id).first()
    if not grocery_list:
        return False
    
    db.delete(grocery_list)
    db.commit()
    
    logger.info(f"Deleted grocery list {list_id}")
    return True


def format_for_instacart(grocery_list: GroceryList) -> List[Dict[str, Any]]:
    """
    Format grocery list items for Instacart API compatibility.
    Returns list of items with name, display_text, and measurements.
    
    Instacart API expects:
    {
        "name": "milk",  # Generic product name for matching
        "display_text": "whole milk",  # Full description
        "measurements": [{"quantity": 2, "unit": "cups"}]
    }
    """
    instacart_items = []
    
    for item in grocery_list.items:
        name_lower = item.ingredient_name.lower()
        
        measurements = []
        if item.quantity and item.unit:
            measurements.append({
                "quantity": item.quantity,
                "unit": item.unit,
            })
        
        instacart_item = {
            "name": name_lower,
            "display_text": item.ingredient_name,
            "measurements": measurements,
        }
        
        if item.retail_package:
            instacart_item["suggested_package"] = item.retail_package
            if item.retail_package_count and item.retail_package_count > 1:
                instacart_item["suggested_quantity"] = item.retail_package_count
        
        instacart_items.append(instacart_item)
    
    return instacart_items
