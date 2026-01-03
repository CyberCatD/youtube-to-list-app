// src/components/RecipeDetail.tsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import type { Recipe } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const formatDuration = (isoDuration: string | null): string => {
  if (!isoDuration) return '';
  
  const match = isoDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return isoDuration;
  
  const hours = match[1] ? parseInt(match[1]) : 0;
  const minutes = match[2] ? parseInt(match[2]) : 0;
  const seconds = match[3] ? parseInt(match[3]) : 0;
  
  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
  if (minutes > 0) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
  if (seconds > 0 && hours === 0) parts.push(`${seconds} second${seconds > 1 ? 's' : ''}`);
  
  return parts.length > 0 ? parts.join(' ') : '0 minutes';
};

const formatQuantityAsFraction = (quantity: number | null): string => {
  if (quantity === null || quantity === 0) return '??';
  
  const fractionMap: Record<number, string> = {
    0.125: '1/8',
    0.25: '1/4',
    0.333: '1/3',
    0.375: '3/8',
    0.5: '1/2',
    0.625: '5/8',
    0.666: '2/3',
    0.667: '2/3',
    0.75: '3/4',
    0.875: '7/8',
  };
  
  const whole = Math.floor(quantity);
  const decimal = Math.round((quantity - whole) * 1000) / 1000;
  
  if (decimal === 0) {
    return whole.toString();
  }
  
  const fraction = fractionMap[decimal];
  if (fraction) {
    return whole > 0 ? `${whole} ${fraction}` : fraction;
  }
  
  if (quantity % 1 !== 0) {
    return quantity.toFixed(2).replace(/\.?0+$/, '');
  }
  
  return quantity.toString();
};

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
          convertedUnit = 'tablespoons';
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
  const [isMetric, setIsMetric] = useState(false);
  const [imageError, setImageError] = useState(false); // Correctly define imageError state

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
    <Card className="mx-auto p-4 md:p-8 shadow-lg max-w-4xl" style={{ backgroundColor: 'white' }}>
      {recipe.main_image_url && !imageError ? (
        <img
          src={recipe.main_image_url}
          alt={recipe.name}
          className="w-full h-64 object-cover rounded-t-lg mb-6"
          onError={() => {
            console.error(`Failed to load image: ${recipe?.main_image_url}`);
            setImageError(true);
          }}
        />
      ) : (recipe.main_image_url && imageError) ? (
        <div className="w-full h-64 flex items-center justify-center bg-gray-200 text-gray-500 rounded-t-lg mb-6">
          Image not available
        </div>
      ) : null}
      <CardHeader className="pb-4">
        <CardTitle className="text-4xl font-extrabold text-gray-900 mb-2 leading-tight">{recipe.name}</CardTitle>
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {recipe.category && <Badge variant="secondary" className="text-md px-3 py-1">{recipe.category}</Badge>}
          {recipe.cuisine && <Badge variant="secondary" className="text-md px-3 py-1">{recipe.cuisine}</Badge>}
          {recipe.servings && <Badge variant="outline" className="text-md px-3 py-1">Serves: {recipe.servings}</Badge>}
          <div className="flex items-center space-x-2 ml-auto">
            <Switch
              id="unit-toggle"
              checked={isMetric}
              onCheckedChange={setIsMetric}
            />
            <Label htmlFor="unit-toggle" className="text-md font-medium">{isMetric ? 'Metric' : 'Imperial'}</Label>
          </div>
        </div>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-gray-700 text-base border-t pt-4 mt-4">
            {recipe.prep_time && <p><strong className="font-semibold">Prep:</strong> {formatDuration(recipe.prep_time)}</p>}
            {recipe.cook_time && <p><strong className="font-semibold">Cook:</strong> {formatDuration(recipe.cook_time)}</p>}
            {recipe.total_time && <p><strong className="font-semibold">Total:</strong> {formatDuration(recipe.total_time)}</p>}
            {recipe.calories && <p><strong className="font-semibold">Calories:</strong> {recipe.calories}</p>}
        </div>
      </CardHeader>

      <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-6">
        {/* Ingredients Column */}
        <div className="md:col-span-1">
          <h2 className="text-2xl font-bold mb-4 border-b pb-2 text-gray-800">Ingredients</h2>
          <ul className="space-y-4 text-gray-800 text-lg">
            {recipe.ingredients.map((item, index) => {
              const { quantity, unit } = convertUnits(item.quantity, item.unit, isMetric);
              const hasQuantity = quantity !== null && quantity !== 0;
              const hasUnit = unit !== null && unit !== '' && unit !== 'quantity not specified';
              const formattedQty = hasQuantity ? formatQuantityAsFraction(quantity) : '??';
              const displayUnit = hasUnit ? unit : '';
              return (
                <li key={index} className="grid grid-cols-3 gap-2 items-baseline">
                  <div className="font-bold col-span-1">
                    {formattedQty} {displayUnit}
                  </div>
                  <div className="col-span-2">
                    {item.ingredient.name}
                    {item.notes && <span className="text-gray-600 text-sm block">({item.notes})</span>}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Instructions Column */}
        <div className="md:col-span-2">
          <h2 className="text-2xl font-bold mb-4 border-b pb-2 text-gray-800">Instructions</h2>
          <div className="space-y-6 text-gray-800 text-lg">
            {(() => {
              let currentSection = "";
              return recipe.instructions.map((step) => {
                const showSection = step.section_name && step.section_name !== currentSection;
                if (showSection) {
                  currentSection = step.section_name!;
                }
                return (
                  <div key={step.step_number}>
                    {showSection && <h3 className="text-xl font-bold mt-8 mb-3 border-b pb-1 text-gray-800">{currentSection}</h3>}
                    <div className="flex items-start">
                      <span className={`font-bold text-lg mr-4 ${isMetric ? 'text-red-400' : 'text-blue-600'}`}>{step.step_number}.</span>
                      <p className="flex-1">{step.description}</p>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      </CardContent>
       <div className="mt-10 text-center border-t pt-6">
          <Link to={recipe.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 text-lg font-medium">
            Watch the original video on YouTube
          </Link>
        </div>
    </Card>
  );
};

export default RecipeDetail;
