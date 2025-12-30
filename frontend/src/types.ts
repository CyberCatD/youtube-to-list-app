// src/types.ts

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
  prep_time: string | null;
  cook_time: string | null;
  total_time: string | null;
  servings: string | null;
  category: string | null;
  cuisine: string | null;
  calories: number | null;
  card_color: string | null;
  created_at: string; // Dates are strings in JSON
  ingredients: RecipeIngredient[];
  instructions: Instruction[];
}
