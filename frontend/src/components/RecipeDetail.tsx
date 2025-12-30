// src/components/RecipeDetail.tsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import type { Recipe } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

// Utility function for unit conversions
const convertUnits = (quantity: number | null, unit: string | null, toMetric: boolean) => {
  if (quantity === null || unit === null) {
    return { quantity, unit };
  }

  let convertedQuantity = quantity;
  let convertedUnit = unit;

  const lowerCaseUnit = unit.toLowerCase();

  if (toMetric) {
    switch (lowerCaseUnit) {
      case 'cup':
      case 'cups':
        convertedQuantity = quantity * 240; // 1 cup = 240 ml
        convertedUnit = 'ml';
        break;
      case 'fl oz':
      case 'fluid ounce':
        convertedQuantity = quantity * 29.5735; // 1 fl oz = 29.5735 ml
        convertedUnit = 'ml';
        break;
      case 'oz':
      case 'ounce':
      case 'ounces':
        convertedQuantity = quantity * 28.35; // 1 oz = 28.35 g
        convertedUnit = 'g';
        break;
      case 'lb':
      case 'lbs':
      case 'pound':
      case 'pounds':
        convertedQuantity = quantity * 453.592; // 1 lb = 453.592 g
        convertedUnit = 'g';
        break;
      case 'tsp':
      case 'teaspoon':
        convertedQuantity = quantity * 4.929; // 1 tsp = 4.929 ml
        convertedUnit = 'ml';
        break;
      case 'tbsp':
      case 'tablespoon':
        convertedQuantity = quantity * 14.79; // 1 tbsp = 14.79 ml
        convertedUnit = 'ml';
        break;
      // Add more metric conversions as needed
    }
  } else { // Convert to Imperial
    switch (lowerCaseUnit) {
      case 'ml':
        if (quantity >= 236) { // ~1 cup
          convertedQuantity = quantity / 236.588;
          convertedUnit = 'cups';
        } else if (quantity >= 14) { // ~1 tbsp
          convertedQuantity = quantity / 14.79;
          convertedUnit = 'tbsp';
        } else if (quantity >= 4) { // ~1 tsp
          convertedQuantity = quantity / 4.929;
          convertedUnit = 'tsp';
        } else { 
          convertedQuantity = quantity; // Keep as ml if very small
          convertedUnit = 'ml';
        }
        break;
      case 'g':
      case 'gram':
      case 'grams':
        if (quantity >= 450) { // ~1 lb
          convertedQuantity = quantity / 453.592;
          convertedUnit = 'lbs';
        } else if (quantity >= 28) { // ~1 oz
          convertedQuantity = quantity / 28.35;
          convertedUnit = 'oz';
        } else { 
          convertedQuantity = quantity; // Keep as g if very small
          convertedUnit = 'g';
        }
        break;
      // Add more imperial conversions as needed
    }
  }

  // Round to 2 decimal places if it's not a whole number
  if (convertedQuantity !== null && convertedQuantity % 1 !== 0) {
    convertedQuantity = parseFloat(convertedQuantity.toFixed(2));
  }

  return { quantity: convertedQuantity, unit: convertedUnit };
};

const RecipeDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMetric, setIsMetric] = useState(false); // New state for unit system

  useEffect(() => {
    if (!id) return;

    const fetchRecipe = async () => {
      try {
        const response = await axios.get(`/api/v1/recipes/${id}`);
        setRecipe(response.data);
      } catch (err) {
        setError('Failed to fetch recipe details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecipe();
  }, [id]);

  if (loading) return <p className="text-center text-gray-500">Loading recipe...</p>;
  if (error) return <p className="text-center text-red-500">{error}</p>;
  if (!recipe) return <p className="text-center text-gray-500">Recipe not found.</p>;

  return (
    <Card className="mx-auto p-4 md:p-8 shadow-lg" style={{ backgroundColor: recipe.card_color || '#EAEAEA' }}>
      <CardHeader className="mb-6">
        <CardTitle className="text-4xl font-bold text-gray-800 mb-2">{recipe.name}</CardTitle>
        <CardDescription className="flex flex-wrap gap-2 mb-4">
          {recipe.category && <Badge variant="secondary">{recipe.category}</Badge>}
          {recipe.cuisine && <Badge variant="secondary">{recipe.cuisine}</Badge>}
          {recipe.servings && <Badge variant="outline">Serves: {recipe.servings}</Badge>}
        </CardDescription>
        <div className="flex flex-wrap gap-4 text-gray-700 text-lg">
            {recipe.prep_time && <p><strong>Prep:</strong> {recipe.prep_time}</p>}
            {recipe.cook_time && <p><strong>Cook:</strong> {recipe.cook_time}</p>}
            {recipe.total_time && <p><strong>Total:</strong> {recipe.total_time}</p>}
            {recipe.calories && <p><strong>Calories:</strong> {recipe.calories}</p>}
        </div>
      </CardHeader>

      <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Ingredients Column */}
        <div className="md:col-span-1">
          <div className="flex items-center justify-between mb-4 border-b pb-2">
            <h2 className="text-2xl font-semibold">Ingredients</h2>
            <div className="flex items-center space-x-2">
              <Switch
                id="unit-toggle"
                checked={isMetric}
                onCheckedChange={setIsMetric}
              />
              <Label htmlFor="unit-toggle">{isMetric ? 'Metric' : 'Imperial'}</Label>
            </div>
          </div>
          <ul className="space-y-3">
            {recipe.ingredients.map((item, index) => {
              const { quantity, unit } = convertUnits(item.quantity, item.unit, isMetric);
              return (
                <li key={index} className="grid grid-cols-3 gap-2 items-start text-gray-800">
                  <div className="font-semibold col-span-1">
                    {quantity} {unit}
                  </div>
                  <div className="col-span-2">
                    {item.ingredient.name}
                    {item.notes && <span className="text-gray-500 text-sm block">{item.notes}</span>}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Instructions Column */}
        <div className="md:col-span-2">
          <h2 className="text-2xl font-semibold mb-4 border-b pb-2">Instructions</h2>
          <div className="space-y-4 text-gray-800">
            {(() => {
              let currentSection = "";
              return recipe.instructions.map((step) => {
                const showSection = step.section_name && step.section_name !== currentSection;
                if (showSection) {
                  currentSection = step.section_name!;
                }
                return (
                  <div key={step.step_number}>
                    {showSection && <h3 className="text-xl font-semibold mt-6 mb-2 border-b">{currentSection}</h3>}
                    <div className="flex items-start">
                      <span className="font-bold text-lg mr-4 text-blue-500">{step.step_number}.</span>
                      <p>{step.description}</p>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      </CardContent>
       <div className="mt-8 text-center">
          <Link to={recipe.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
            Watch the original video on YouTube
          </Link>
        </div>
    </Card>
  );
};

export default RecipeDetail;
