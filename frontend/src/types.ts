// src/types.ts

export interface Tag {
  id: number;
  name: string;
  tag_type: string;
}

export interface Ingredient {
  name: string;
}

export interface RecipeIngredient {
  ingredient: Ingredient;
  quantity: number | null;
  unit: string | null;
  notes: string | null;
}

export interface Instruction {
  step_number: number;
  section_name: string | null;
  description: string;
}

export interface Recipe {
  id: number;
  name: string;
  source_url: string;
  source_type: string | null;
  prep_time: string | null;
  cook_time: string | null;
  total_time: string | null;
  servings: string | null;
  category: string | null;
  cuisine: string | null;
  calories: number | null;
  main_image_url: string | null;
  created_at: string;
  ingredients: RecipeIngredient[];
  instructions: Instruction[];
  tags: Tag[];
}

export interface GroceryListItem {
  id: number;
  ingredient_name: string;
  quantity: number | null;
  unit: string | null;
  category: string | null;
  is_checked: boolean;
  recipe_ids: number[] | null;
  retail_package: string | null;
  retail_package_count: number | null;
  exact_amount: string | null;
}

export interface RecipeSummary {
  id: number;
  name: string;
  main_image_url: string | null;
}

export interface GroceryList {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  items: GroceryListItem[];
  recipes: RecipeSummary[];
}
