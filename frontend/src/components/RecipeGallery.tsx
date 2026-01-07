// src/components/RecipeGallery.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import type { Recipe } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trash2, RotateCcw, Youtube, Globe, Instagram, Facebook } from 'lucide-react';

const CATEGORIES = ['All', 'Breakfast', 'Lunch', 'Dinner', 'Appetizer', 'Main Course', 'Dessert', 'Snack', 'Beverage'];

const getSourceIcon = (sourceType: string | null) => {
  switch (sourceType) {
    case 'youtube':
      return <Youtube size={14} className="text-red-500" />;
    case 'web':
      return <Globe size={14} className="text-blue-500" />;
    case 'instagram':
      return <Instagram size={14} className="text-pink-500" />;
    case 'tiktok':
      return <span className="text-xs font-bold text-black">TT</span>;
    case 'facebook':
      return <Facebook size={14} className="text-blue-600" />;
    default:
      return <Globe size={14} className="text-gray-500" />;
  }
};

const RecipeGallery = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [trashCount, setTrashCount] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState(false);

  const fetchRecipes = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/recipes/');
      console.log("--- DEBUG: FRONTEND DATA ---", response.data);
      setRecipes(response.data.recipes);
    } catch (err) {
      setError('Failed to fetch recipes. Is the backend server running?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrashCount = async () => {
    try {
      const response = await axios.get('/api/v1/recipes/trash/count');
      setTrashCount(response.data.count);
    } catch (err) {
      console.error('Failed to fetch trash count:', err);
    }
  };

  useEffect(() => {
    fetchRecipes();
    fetchTrashCount();
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const urlInput = event.currentTarget.elements.namedItem('url') as HTMLInputElement;
    const url = urlInput.value.trim();
    
    if (!url) {
      alert('Please enter a URL');
      return;
    }
    
    setIsProcessing(true);
    
    try {
      const response = await axios.post('/api/v1/youtube/process-url', { url });
      urlInput.value = '';
      fetchRecipes();
      const sourceLabel = response.data.source_type === 'youtube' ? 'YouTube' : 
                          response.data.source_type === 'web' ? 'website' : 'source';
      alert(`✅ Recipe imported from ${sourceLabel}: ${response.data.recipe_name}`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to process URL';
      alert(`❌ Error: ${errorMsg}`);
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (recipeId: number, recipeName: string) => {
    if (deleteConfirm === recipeId) {
      // Second click - confirm deletion (move to trash)
      try {
        await axios.delete(`/api/v1/recipes/${recipeId}`);
        setRecipes(recipes.filter(r => r.id !== recipeId));
        setDeleteConfirm(null);
        fetchTrashCount(); // Update trash count
        alert(`🗑️ Moved to trash: ${recipeName}`);
      } catch (err) {
        alert('❌ Failed to delete recipe');
        console.error(err);
      }
    } else {
      // First click - show confirmation
      setDeleteConfirm(recipeId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const handleUndo = async () => {
    try {
      const response = await axios.post('/api/v1/recipes/trash/restore');
      fetchRecipes(); // Refresh recipe list
      fetchTrashCount(); // Update trash count
      alert(`✅ Restored: ${response.data.name}`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'No recipes in trash to restore';
      alert(`ℹ️ ${errorMsg}`);
      console.error(err);
    }
  };

  const filteredRecipes = selectedCategory === 'All' 
    ? recipes 
    : recipes.filter(r => r.category === selectedCategory);

  return (
    <div className="relative">
      {/* URL Input Form - Mobile Optimized */}
      <form onSubmit={handleSubmit} className="mb-6 md:mb-8">
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-0 sm:justify-center">
          <input 
            type="text" 
            name="url" 
            placeholder="Paste any recipe URL..." 
            className="w-full sm:w-1/2 p-3 border rounded-lg sm:rounded-l-md sm:rounded-r-none text-base"
            disabled={isProcessing}
          />
          <button 
            type="submit" 
            className={`w-full sm:w-auto px-6 py-3 rounded-lg sm:rounded-l-none sm:rounded-r-md transition-colors ${
              isProcessing 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700'
            } text-white font-medium`}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Import Recipe'}
          </button>
        </div>
        
        {/* Undo/Restore Button - Full width on mobile */}
        {trashCount > 0 && (
          <button
            type="button"
            onClick={handleUndo}
            className="w-full sm:w-auto mt-3 sm:mt-0 sm:ml-4 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white px-4 py-3 sm:py-2 rounded-lg sm:rounded-md transition-colors"
            title={`Restore most recently deleted recipe (${trashCount} in trash)`}
          >
            <RotateCcw size={18} />
            Undo Delete ({trashCount})
          </button>
        )}
      </form>

      {/* Category Filter - Horizontal Scroll on Mobile */}
      <div className="mb-6 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        <div className="flex gap-2 sm:flex-wrap sm:justify-center min-w-max sm:min-w-0">
          {CATEGORIES.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300 active:bg-gray-400'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-center text-gray-500">Loading recipes...</p>}
      {error && <p className="text-center text-red-500">{error}</p>}
      
      {!loading && !error && (
        <>
          <p className="text-center text-gray-600 mb-4 text-sm md:text-base">
            Showing {filteredRecipes.length} of {recipes.length} recipes
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8">
            {filteredRecipes.map((recipe) => (
              <div key={recipe.id} className="relative group">
                <Link to={`/recipe/${recipe.id}`} className="block">
                  <Card className="hover:shadow-xl active:shadow-lg transition-shadow duration-300">
                    <div className="relative">
                      {recipe.main_image_url ? (
                        <img 
                          src={recipe.main_image_url} 
                          alt={recipe.name}
                          className="w-full h-40 sm:h-48 object-cover rounded-t-lg"
                          onError={(e) => { 
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const placeholder = target.nextElementSibling as HTMLElement;
                            if (placeholder) placeholder.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div 
                        className="w-full h-40 sm:h-48 bg-gradient-to-br from-gray-100 to-gray-200 rounded-t-lg items-center justify-center text-gray-400"
                        style={{ display: recipe.main_image_url ? 'none' : 'flex' }}
                      >
                        <span className="text-4xl">🍽️</span>
                      </div>
                      <div className="absolute bottom-2 left-2 bg-white/90 rounded-full p-1.5 shadow">
                        {getSourceIcon(recipe.source_type)}
                      </div>
                    </div>
                    <CardHeader>
                      <CardTitle className="text-xl font-semibold text-gray-800">{recipe.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {recipe.category && (
                        <Badge variant="secondary" className="mb-2">{recipe.category}</Badge>
                      )}
                      {recipe.cuisine && (
                        <Badge variant="outline" className="ml-2 mb-2">{recipe.cuisine}</Badge>
                      )}
                      <p className="text-sm text-gray-600 mt-2">
                        {recipe.total_time && `⏱️ ${recipe.total_time}`}
                        {recipe.servings && ` • 🍽️ ${recipe.servings} servings`}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
                
                {/* Delete Button */}
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleDelete(recipe.id, recipe.name);
                  }}
                  className={`absolute top-2 right-2 p-2 rounded-full transition-all ${
                    deleteConfirm === recipe.id
                      ? 'bg-red-600 text-white scale-125 shadow-xl'
                      : 'bg-white text-red-500 opacity-0 group-hover:opacity-100'
                  } hover:bg-red-600 hover:text-white shadow-lg z-10`}
                  title={deleteConfirm === recipe.id ? 'Click again to confirm deletion' : 'Delete recipe'}
                >
                  <Trash2 size={20} />
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default RecipeGallery;
