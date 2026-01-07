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
