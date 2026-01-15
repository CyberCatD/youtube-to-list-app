import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import type { Recipe, GroceryList } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { RecipeDetailSkeleton } from "@/components/ui/skeleton";
import { Pencil, Check, X, Upload, RefreshCw, ImageIcon, ShoppingCart, Plus, Clock, Flame, Users, Minus, CheckCircle2, Circle } from 'lucide-react';

const formatDurationLong = (isoDuration: string | null): string => {
  if (!isoDuration) return '';
  
  const match = isoDuration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return isoDuration;
  
  const hours = match[1] ? parseInt(match[1]) : 0;
  const minutes = match[2] ? parseInt(match[2]) : 0;
  
  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
  if (minutes > 0) parts.push(`${minutes} minute${minutes > 1 ? 's' : ''}`);
  
  return parts.length > 0 ? parts.join(' ') : '0 minutes';
};

const parseServings = (servings: string | null): number => {
  if (!servings) return 4;
  const match = servings.match(/\d+/);
  return match ? parseInt(match[0]) : 4;
};

const formatQuantityAsFraction = (quantity: number | null): string => {
  if (quantity === null || quantity === 0) return '';
  
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
  
  const matchedFraction = fractionMap.find(f => Math.abs(f.value - decimal) < 0.01);
  
  if (matchedFraction) {
    return whole > 0 ? `${whole} ${matchedFraction.display}` : matchedFraction.display;
  }
  
  if (quantity % 1 !== 0) {
    return quantity.toFixed(2).replace(/\.?0+$/, '');
  }
  
  return quantity.toString();
};

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
        convertedQuantity = quantity * 240;
        convertedUnit = 'ml';
        break;
      case 'fl oz':
      case 'fluid ounce':
        convertedQuantity = quantity * 29.5735;
        convertedUnit = 'ml';
        break;
      case 'oz':
      case 'ounce':
      case 'ounces':
        convertedQuantity = quantity * 28.35;
        convertedUnit = 'g';
        break;
      case 'lb':
      case 'lbs':
      case 'pound':
      case 'pounds':
        convertedQuantity = quantity * 453.592;
        convertedUnit = 'g';
        break;
      case 'tsp':
      case 'teaspoon':
        convertedQuantity = quantity * 4.929;
        convertedUnit = 'ml';
        break;
      case 'tbsp':
      case 'tablespoon':
        convertedQuantity = quantity * 14.79;
        convertedUnit = 'ml';
        break;
    }
  } else {
    switch (lowerCaseUnit) {
      case 'ml':
        if (quantity >= 236) {
          convertedQuantity = quantity / 236.588;
          convertedUnit = 'cups';
        } else if (quantity >= 14) {
          convertedQuantity = quantity / 14.79;
          convertedUnit = 'tbsp';
        } else if (quantity >= 4) {
          convertedQuantity = quantity / 4.929;
          convertedUnit = 'tsp';
        }
        break;
      case 'g':
      case 'gram':
      case 'grams':
        if (quantity >= 450) {
          convertedQuantity = quantity / 453.592;
          convertedUnit = 'lbs';
        } else if (quantity >= 28) {
          convertedQuantity = quantity / 28.35;
          convertedUnit = 'oz';
        }
        break;
    }
  }

  if (convertedQuantity !== null && convertedQuantity % 1 !== 0) {
    convertedQuantity = parseFloat(convertedQuantity.toFixed(2));
  }

  return { quantity: convertedQuantity, unit: convertedUnit };
};

const fetchRecipe = async (id: string): Promise<Recipe> => {
  const response = await axios.get(`/api/v1/recipes/${id}`);
  return response.data;
};

const RecipeDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const { data: recipe, isLoading, error } = useQuery({
    queryKey: ['recipe', id],
    queryFn: () => fetchRecipe(id!),
    enabled: !!id,
  });

  const [isMetric, setIsMetric] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [isFetchingImage, setIsFetchingImage] = useState(false);
  const [nutrition, setNutrition] = useState<any>(null);
  const [loadingNutrition, setLoadingNutrition] = useState(false);
  const [showNutrition, setShowNutrition] = useState(false);
  const [groceryLists, setGroceryLists] = useState<GroceryList[]>([]);
  const [showGroceryMenu, setShowGroceryMenu] = useState(false);
  const [addingToList, setAddingToList] = useState(false);
  
  const originalServings = recipe ? parseServings(recipe.servings) : 4;
  const [portions, setPortions] = useState(originalServings);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (recipe) {
      setPortions(parseServings(recipe.servings));
    }
  }, [recipe]);

  const scaleFactor = portions / originalServings;

  const toggleStep = (stepNumber: number) => {
    setCompletedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepNumber)) {
        next.delete(stepNumber);
      } else {
        next.add(stepNumber);
      }
      return next;
    });
  };

  const fetchGroceryLists = async () => {
    try {
      const response = await axios.get('/api/v1/grocery-lists/');
      setGroceryLists(response.data);
    } catch (err) {
      console.error('Failed to fetch grocery lists:', err);
    }
  };

  const handleAddToNewList = async () => {
    if (!recipe) return;
    setAddingToList(true);
    try {
      const response = await axios.post('/api/v1/grocery-lists/', {
        name: `Grocery List - ${new Date().toLocaleDateString()}`,
        recipe_ids: [recipe.id],
      });
      setShowGroceryMenu(false);
      navigate(`/grocery-lists/${response.data.id}`);
    } catch (err) {
      console.error('Failed to create grocery list:', err);
      alert('Failed to create grocery list');
    } finally {
      setAddingToList(false);
    }
  };

  const handleAddToExistingList = async (listId: number) => {
    if (!recipe) return;
    setAddingToList(true);
    try {
      await axios.post(`/api/v1/grocery-lists/${listId}/recipes`, {
        recipe_id: recipe.id,
      });
      setShowGroceryMenu(false);
      navigate(`/grocery-lists/${listId}`);
    } catch (err) {
      console.error('Failed to add to grocery list:', err);
      alert('Failed to add to grocery list');
    } finally {
      setAddingToList(false);
    }
  };

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
      queryClient.setQueryData(['recipe', id], response.data);
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
      queryClient.setQueryData(['recipe', id], response.data);
      setImageError(false);
      setImageLoaded(false);
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
        queryClient.setQueryData(['recipe', id], response.data);
        setImageError(false);
        setImageLoaded(false);
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

  if (isLoading) return <RecipeDetailSkeleton />;
  if (error) return <p className="text-center text-red-500">Failed to fetch recipe details.</p>;
  if (!recipe) return <p className="text-center text-gray-500">Recipe not found.</p>;

  const completedCount = completedSteps.size;
  const totalSteps = recipe.instructions.length;
  const progressPercent = totalSteps > 0 ? (completedCount / totalSteps) * 100 : 0;

  return (
    <Card className="mx-auto shadow-lg max-w-5xl">
      {recipe.main_image_url && !imageError ? (
        <div className="relative group">
          {!imageLoaded && (
            <div className="absolute inset-0 h-64 sm:h-80 bg-muted animate-pulse rounded-t-lg" />
          )}
          <img
            src={recipe.main_image_url}
            alt={recipe.name}
            loading="lazy"
            decoding="async"
            className={`w-full h-64 sm:h-80 object-cover rounded-t-lg transition-opacity duration-300 ${
              imageLoaded ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={() => setImageLoaded(true)}
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
        <div className="w-full h-64 sm:h-80 flex flex-col items-center justify-center bg-gradient-to-br from-muted to-muted/80 rounded-t-lg gap-4">
          <ImageIcon size={48} className="text-muted-foreground" />
          <p className="text-muted-foreground text-sm">No image available</p>
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

      <CardHeader className="p-4 md:p-6">
        <div className="flex items-start gap-2 mb-3">
          {isEditingName ? (
            <div className="flex-1 flex items-center gap-2">
              <input
                type="text"
                value={editedName}
                onChange={(e) => setEditedName(e.target.value)}
                className="flex-1 text-2xl md:text-3xl font-extrabold border-b-2 border-primary bg-transparent focus:outline-none"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveName();
                  if (e.key === 'Escape') handleCancelEdit();
                }}
              />
              <button onClick={handleSaveName} disabled={isSaving} className="p-2 text-green-600 hover:bg-green-100 rounded-full" title="Save">
                <Check size={24} />
              </button>
              <button onClick={handleCancelEdit} className="p-2 text-red-600 hover:bg-red-100 rounded-full" title="Cancel">
                <X size={24} />
              </button>
            </div>
          ) : (
            <>
              <CardTitle className="text-2xl md:text-4xl font-extrabold leading-tight flex-1">{recipe.name}</CardTitle>
              <button onClick={handleEditName} className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full" title="Edit recipe name">
                <Pencil size={20} />
              </button>
            </>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 mb-4">
          {recipe.category && <Badge variant="secondary" className="text-sm px-3 py-1">{recipe.category}</Badge>}
          {recipe.cuisine && <Badge variant="secondary" className="text-sm px-3 py-1">{recipe.cuisine}</Badge>}
        </div>

        <div className="flex flex-wrap items-center gap-4 md:gap-6 py-3 px-4 bg-secondary rounded-lg text-sm md:text-base">
          {recipe.total_time && (
            <span className="flex items-center gap-1.5">
              <Clock size={18} className="text-blue-500" />
              {formatDurationLong(recipe.total_time)}
            </span>
          )}
          {recipe.calories !== null && recipe.calories > 0 && (
            <span className="flex items-center gap-1.5">
              <Flame size={18} className="text-orange-500" />
              {recipe.calories} cal
            </span>
          )}
          <span className="flex items-center gap-1.5">
            <Users size={18} className="text-green-500" />
            {portions} serving{portions !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center space-x-2 ml-auto">
            <Switch id="unit-toggle" checked={isMetric} onCheckedChange={setIsMetric} />
            <Label htmlFor="unit-toggle" className="text-sm font-medium">{isMetric ? 'Metric' : 'Imperial'}</Label>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 mt-4">
          <button onClick={handleToggleNutrition} className="flex items-center gap-2 text-primary hover:text-primary/80 font-medium transition-colors text-sm">
            {loadingNutrition ? 'Loading...' : showNutrition ? 'Hide Nutrition' : 'Show Nutrition'}
          </button>
          
          <div className="relative">
            <button
              onClick={() => {
                if (!showGroceryMenu) fetchGroceryLists();
                setShowGroceryMenu(!showGroceryMenu);
              }}
              disabled={addingToList}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 text-sm"
            >
              <ShoppingCart size={16} />
              <span>{addingToList ? 'Adding...' : 'Add to List'}</span>
            </button>

            {showGroceryMenu && (
              <div className="absolute top-full left-0 mt-2 w-64 bg-card rounded-lg shadow-lg border border-border z-10">
                <div className="p-2">
                  <button onClick={handleAddToNewList} disabled={addingToList} className="w-full flex items-center gap-2 p-2 text-left text-green-600 hover:bg-secondary rounded-lg">
                    <Plus size={18} />
                    <span>Create new list</span>
                  </button>
                  {groceryLists.length > 0 && (
                    <>
                      <div className="border-t border-border my-2" />
                      <p className="px-2 py-1 text-xs text-muted-foreground font-medium">Add to existing list:</p>
                      {groceryLists.slice(0, 5).map(list => (
                        <button key={list.id} onClick={() => handleAddToExistingList(list.id)} disabled={addingToList} className="w-full flex items-center gap-2 p-2 text-left hover:bg-secondary rounded-lg">
                          <ShoppingCart size={16} className="text-muted-foreground" />
                          <span className="truncate">{list.name}</span>
                        </button>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {showNutrition && nutrition && (
          <div className="mt-4 p-4 bg-secondary rounded-lg border border-border">
            <h3 className="font-bold text-lg mb-1 border-b border-border pb-2">Nutrition Facts</h3>
            <p className="text-sm text-muted-foreground mb-1">{nutrition.servings} serving(s) per recipe</p>
            <div className="grid grid-cols-4 sm:grid-cols-7 gap-3 text-center mt-3">
              <div className="p-2">
                <p className="text-xl font-bold">{Math.round(nutrition.per_serving.calories)}</p>
                <p className="text-xs text-muted-foreground">Cal</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{nutrition.per_serving.protein}g</p>
                <p className="text-xs text-muted-foreground">Protein</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{nutrition.per_serving.carbs}g</p>
                <p className="text-xs text-muted-foreground">Carbs</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{nutrition.per_serving.fat}g</p>
                <p className="text-xs text-muted-foreground">Fat</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{nutrition.per_serving.fiber}g</p>
                <p className="text-xs text-muted-foreground">Fiber</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{nutrition.per_serving.sugar}g</p>
                <p className="text-xs text-muted-foreground">Sugar</p>
              </div>
              <div className="p-2">
                <p className="text-xl font-bold">{Math.round(nutrition.per_serving.sodium)}mg</p>
                <p className="text-xs text-muted-foreground">Sodium</p>
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-4 md:p-6 pt-0">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-24">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl md:text-2xl font-bold">Ingredients</h2>
                <div className="flex items-center gap-2 bg-secondary rounded-full px-2 py-1">
                  <button
                    onClick={() => setPortions(Math.max(1, portions - 1))}
                    className="p-1 rounded-full hover:bg-muted transition-colors"
                    disabled={portions <= 1}
                  >
                    <Minus size={16} className={portions <= 1 ? 'text-muted-foreground/50' : 'text-muted-foreground'} />
                  </button>
                  <span className="w-8 text-center font-semibold">{portions}</span>
                  <button
                    onClick={() => setPortions(portions + 1)}
                    className="p-1 rounded-full hover:bg-muted transition-colors"
                  >
                    <Plus size={16} className="text-muted-foreground" />
                  </button>
                </div>
              </div>
              
              <ul className="space-y-3">
                {recipe.ingredients.map((item, index) => {
                  const scaledQuantity = item.quantity ? item.quantity * scaleFactor : null;
                  const { quantity, unit } = convertUnits(scaledQuantity, item.unit, isMetric);
                  const hasQuantity = quantity !== null && quantity > 0;
                  const hasUnit = unit !== null && unit !== '';
                  
                  let quantityDisplay = '';
                  if (hasQuantity) {
                    quantityDisplay = formatQuantityAsFraction(quantity);
                    if (hasUnit) {
                      quantityDisplay += ' ' + unit;
                    }
                  } else if (!item.notes) {
                    quantityDisplay = 'to taste';
                  }
                  
                  return (
                    <li key={index} className="flex gap-3 items-baseline py-2 border-b border-border last:border-0">
                      <div className="font-semibold text-primary min-w-[80px] text-right text-sm md:text-base">
                        {quantityDisplay}
                      </div>
                      <div className="flex-1 text-base md:text-lg">
                        <span className="font-medium">{item.ingredient.name}</span>
                        {item.notes && <span className="text-muted-foreground text-sm md:text-base ml-1">({item.notes})</span>}
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl md:text-2xl font-bold">Instructions</h2>
              <span className="text-sm text-muted-foreground">
                {completedCount} of {totalSteps} steps
              </span>
            </div>
            
            {totalSteps > 0 && (
              <div className="w-full bg-secondary rounded-full h-2 mb-6">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            )}
            
            <div className="space-y-4">
              {(() => {
                let currentSection = "";
                return recipe.instructions.map((step) => {
                  const showSection = step.section_name && step.section_name !== currentSection;
                  if (showSection) {
                    currentSection = step.section_name!;
                  }
                  const isCompleted = completedSteps.has(step.step_number);
                  
                  return (
                    <div key={step.step_number}>
                      {showSection && (
                        <h3 className="text-lg md:text-xl font-bold mt-6 mb-3">{currentSection}</h3>
                      )}
                      <div 
                        className={`flex items-start gap-3 p-3 md:p-4 rounded-lg cursor-pointer transition-all ${
                          isCompleted 
                            ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
                            : 'bg-secondary/50 hover:bg-secondary'
                        }`}
                        onClick={() => toggleStep(step.step_number)}
                      >
                        <button className="mt-0.5 flex-shrink-0">
                          {isCompleted ? (
                            <CheckCircle2 size={24} className="text-green-500" />
                          ) : (
                            <Circle size={24} className="text-muted-foreground/50" />
                          )}
                        </button>
                        <div className="flex-1">
                          <span className="font-semibold text-muted-foreground text-sm">Step {step.step_number}</span>
                          <p className={`mt-1 text-base md:text-lg ${isCompleted ? 'text-muted-foreground line-through' : ''}`}>
                            {step.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          </div>
        </div>

        <div className="mt-8 text-center border-t border-border pt-6">
          <a href={recipe.source_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:text-primary/80 font-medium">
            {recipe.source_type === 'youtube' && 'Watch the original video on YouTube'}
            {recipe.source_type === 'instagram' && 'View the original post on Instagram'}
            {recipe.source_type === 'tiktok' && 'Watch the original video on TikTok'}
            {recipe.source_type === 'facebook' && 'View the original post on Facebook'}
            {recipe.source_type === 'web' && 'View the original recipe'}
            {!recipe.source_type && 'View the original source'}
          </a>
        </div>
      </CardContent>
    </Card>
  );
};

export default RecipeDetail;
