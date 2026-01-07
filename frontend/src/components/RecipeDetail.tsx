// src/components/RecipeDetail.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import type { Recipe } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Pencil, Check, X, Upload, RefreshCw, ImageIcon } from 'lucide-react';

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
  
  const fractionMap: Array<{ value: number; display: string }> = [
    { value: 0.125, display: '1/8' },
    { value: 0.25, display: '1/4' },
    { value: 0.333, display: '1/3' },
    { value: 0.375, display: '3/8' },
    { value: 0.5, display: '1/2' },
    { value: 0.625, display: '5/8' },
    { value: 0.666, display: '2/3' },
    { value: 0.667, display: '2/3' },
    { value: 0.75, display: '3/4' },
    { value: 0.875, display: '7/8' },
  ];
  
  const whole = Math.floor(quantity);
  const decimal = quantity - whole;
  
  if (decimal < 0.001) {
    return whole.toString();
  }
  
  // Find matching fraction with tolerance for floating point errors
  const matchedFraction = fractionMap.find(f => Math.abs(f.value - decimal) < 0.01);
  
  if (matchedFraction) {
    return whole > 0 ? `${whole} ${matchedFraction.display}` : matchedFraction.display;
  }
  
  // If no fraction match, show decimal rounded to 2 places
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
  const [imageError, setImageError] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isFetchingImage, setIsFetchingImage] = useState(false);
  const [nutrition, setNutrition] = useState<any>(null);
  const [loadingNutrition, setLoadingNutrition] = useState(false);
  const [showNutrition, setShowNutrition] = useState(false);

  const fetchNutrition = async () => {
    if (!id || nutrition) return;
    setLoadingNutrition(true);
    try {
      const response = await axios.get(`/api/v1/recipes/${id}/nutrition`);
      setNutrition(response.data);
    } catch (err) {
      console.error('Failed to fetch nutrition:', err);
    } finally {
      setLoadingNutrition(false);
    }
  };

  const handleToggleNutrition = () => {
    if (!showNutrition && !nutrition) {
      fetchNutrition();
    }
    setShowNutrition(!showNutrition);
  };

  const handleEditName = () => {
    if (recipe) {
      setEditedName(recipe.name);
      setIsEditingName(true);
    }
  };

  const handleSaveName = async () => {
    if (!recipe || !editedName.trim()) return;
    
    setIsSaving(true);
    try {
      const response = await axios.patch(`/api/v1/recipes/${recipe.id}`, { name: editedName.trim() });
      setRecipe(response.data);
      setIsEditingName(false);
    } catch (err) {
      console.error('Failed to update recipe name:', err);
      alert('Failed to save recipe name');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditingName(false);
    setEditedName('');
  };

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !recipe) return;
    
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      alert('Image must be less than 5MB');
      return;
    }
    
    setIsUploadingImage(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post(`/api/v1/recipes/${recipe.id}/image`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setRecipe(response.data);
      setImageError(false);
    } catch (err) {
      console.error('Failed to upload image:', err);
      alert('Failed to upload image');
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleFetchImage = async () => {
    if (!recipe) return;
    
    setIsFetchingImage(true);
    try {
      const response = await axios.post(`/api/v1/recipes/${recipe.id}/fetch-image`);
      if (response.data.main_image_url !== recipe.main_image_url) {
        setRecipe(response.data);
        setImageError(false);
        alert('Image updated successfully!');
      } else {
        alert('No new image found. Try uploading your own image.');
      }
    } catch (err) {
      console.error('Failed to fetch image:', err);
      alert('Failed to fetch image');
    } finally {
      setIsFetchingImage(false);
    }
  };

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
        <div className="relative group">
          <img
            src={recipe.main_image_url}
            alt={recipe.name}
            className="w-full h-64 object-cover rounded-t-lg mb-6"
            onError={() => {
              console.error(`Failed to load image: ${recipe?.main_image_url}`);
              setImageError(true);
            }}
          />
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
            <label className="p-2 bg-white/90 rounded-full shadow cursor-pointer hover:bg-white" title="Upload new image">
              <Upload size={18} className="text-gray-600" />
              <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" disabled={isUploadingImage} />
            </label>
          </div>
        </div>
      ) : (
        <div className="w-full h-64 flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-t-lg mb-6 gap-4">
          <ImageIcon size={48} className="text-gray-400" />
          <p className="text-gray-500 text-sm">No image available</p>
          <div className="flex gap-3">
            <button
              onClick={handleFetchImage}
              disabled={isFetchingImage}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw size={16} className={isFetchingImage ? 'animate-spin' : ''} />
              {isFetchingImage ? 'Fetching...' : 'Try to fetch image'}
            </button>
            <label className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <Upload size={16} />
              {isUploadingImage ? 'Uploading...' : 'Upload image'}
              <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" disabled={isUploadingImage} />
            </label>
          </div>
        </div>
      )}
      <CardHeader className="pb-4">
        <div className="flex items-start gap-2 mb-2">
          {isEditingName ? (
            <div className="flex-1 flex items-center gap-2">
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="flex-1 text-3xl font-extrabold text-gray-900 border-b-2 border-blue-500 bg-transparent focus:outline-none"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveName();
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <button
                onClick={handleSaveName}
                disabled={isSaving}
                className="p-2 text-green-600 hover:bg-green-100 rounded-full transition-colors"
                title="Save"
              >
                <Check size={24} />
              </button>
              <button
                onClick={handleCancelEdit}
                className="p-2 text-red-600 hover:bg-red-100 rounded-full transition-colors"
                title="Cancel"
              >
                <X size={24} />
              </button>
            </div>
          ) : (
            <>
              <CardTitle className="text-4xl font-extrabold text-gray-900 leading-tight flex-1">{recipe.name}</CardTitle>
              <button
                onClick={handleEditName}
                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                title="Edit recipe name"
              >
                <Pencil size={20} />
              </button>
            </>
          )}
        </div>
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
            {recipe.calories !== null && recipe.calories > 0 && <p><strong className="font-semibold">Calories:</strong> {recipe.calories}</p>}
        </div>

        <button
          onClick={handleToggleNutrition}
          className="mt-4 flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium transition-colors"
        >
          {loadingNutrition ? 'Loading...' : showNutrition ? 'Hide Nutrition Facts' : 'Show Nutrition Facts'}
        </button>

        {showNutrition && nutrition && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <h3 className="font-bold text-lg mb-1 border-b pb-2">Nutrition Facts</h3>
            <p className="text-sm text-gray-600 mb-1">{nutrition.servings} serving(s) per recipe</p>
            <p className="text-sm font-semibold text-gray-700 mb-3">Amount per serving</p>
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-3 text-center">
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{Math.round(nutrition.per_serving.calories)}</p>
                <p className="text-xs text-gray-500">Calories</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{nutrition.per_serving.protein}g</p>
                <p className="text-xs text-gray-500">Protein</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{nutrition.per_serving.carbs}g</p>
                <p className="text-xs text-gray-500">Carbs</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{nutrition.per_serving.fat}g</p>
                <p className="text-xs text-gray-500">Fat</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{nutrition.per_serving.fiber}g</p>
                <p className="text-xs text-gray-500">Fiber</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{nutrition.per_serving.sugar}g</p>
                <p className="text-xs text-gray-500">Sugar</p>
              </div>
              <div className="p-2">
                <p className="text-2xl font-bold text-gray-800">{Math.round(nutrition.per_serving.sodium)}mg</p>
                <p className="text-xs text-gray-500">Sodium</p>
              </div>
            </div>
            {nutrition.ingredients_missing?.length > 0 && (
              <p className="text-xs text-gray-500 mt-3">
                * Could not find nutrition data for: {nutrition.ingredients_missing.join(', ')}
              </p>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-6">
        {/* Ingredients Column */}
        <div className="md:col-span-1">
          <h2 className="text-2xl font-bold mb-4 border-b pb-2 text-gray-800">Ingredients</h2>
          <ul className="space-y-4 text-gray-800 text-lg">
            {recipe.ingredients.map((item, index) => {
              const { quantity, unit } = convertUnits(item.quantity, item.unit, isMetric);
              const hasQuantity = quantity !== null && quantity > 0;
              const hasUnit = unit !== null && unit !== '';
              
              // Determine what to display for quantity
              let quantityDisplay = '';
              if (hasQuantity) {
                quantityDisplay = formatQuantityAsFraction(quantity);
                if (hasUnit) {
                  quantityDisplay += ' ' + unit;
                }
              } else if (item.notes) {
                // If no quantity but has notes, show "as needed" or similar
                quantityDisplay = '';
              } else {
                // Fallback for no quantity and no notes
                quantityDisplay = 'to taste';
              }
              
              return (
                <li key={index} className="flex gap-3 items-baseline">
                  <div className="font-bold min-w-[100px] text-right">
                    {quantityDisplay}
                  </div>
                  <div className="flex-1">
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
          <a href={recipe.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 text-lg font-medium">
            {recipe.source_type === 'youtube' && 'Watch the original video on YouTube'}
            {recipe.source_type === 'instagram' && 'View the original post on Instagram'}
            {recipe.source_type === 'tiktok' && 'Watch the original video on TikTok'}
            {recipe.source_type === 'facebook' && 'View the original post on Facebook'}
            {recipe.source_type === 'web' && 'View the original recipe'}
            {!recipe.source_type && 'View the original source'}
          </a>
        </div>
    </Card>
  );
};

export default RecipeDetail;
