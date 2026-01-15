import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

const fetchRecipes = async () => {
  const response = await axios.get('/api/v1/recipes/');
  return response.data.recipes as Recipe[];
};

const fetchTrashCount = async () => {
  const response = await axios.get('/api/v1/recipes/trash/count');
  return response.data.count as number;
};

const RecipeGallery = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);

  const { data: recipes = [], isLoading, error } = useQuery({
    queryKey: ['recipes'],
    queryFn: fetchRecipes,
  });

  const { data: trashCount = 0 } = useQuery({
    queryKey: ['trashCount'],
    queryFn: fetchTrashCount,
  });

  const processUrlMutation = useMutation({
    mutationFn: (url: string) => axios.post('/api/v1/youtube/process-url', { url }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      const sourceLabel = response.data.source_type === 'youtube' ? 'YouTube' : 
                          response.data.source_type === 'web' ? 'website' : 'source';
      alert(`Recipe imported from ${sourceLabel}: ${response.data.recipe_name}`);
    },
    onError: (err: any) => {
      const errorMsg = err.response?.data?.detail || 'Failed to process URL';
      alert(`Error: ${errorMsg}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (recipeId: number) => axios.delete(`/api/v1/recipes/${recipeId}`),
    onSuccess: (_, recipeId) => {
      queryClient.setQueryData(['recipes'], (old: Recipe[] | undefined) => 
        old?.filter(r => r.id !== recipeId) ?? []
      );
      queryClient.invalidateQueries({ queryKey: ['trashCount'] });
      setDeleteConfirm(null);
    },
    onError: () => {
      alert('Failed to delete recipe');
    },
  });

  const restoreMutation = useMutation({
    mutationFn: () => axios.post('/api/v1/recipes/trash/restore'),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      queryClient.invalidateQueries({ queryKey: ['trashCount'] });
      alert(`Restored: ${response.data.name}`);
    },
    onError: (err: any) => {
      const errorMsg = err.response?.data?.detail || 'No recipes in trash to restore';
      alert(errorMsg);
    },
  });

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const urlInput = event.currentTarget.elements.namedItem('url') as HTMLInputElement;
    const url = urlInput.value.trim();
    
    if (!url) {
      alert('Please enter a URL');
      return;
    }
    
    processUrlMutation.mutate(url);
    urlInput.value = '';
  };

  const handleDelete = (recipeId: number, recipeName: string) => {
    if (deleteConfirm === recipeId) {
      deleteMutation.mutate(recipeId);
      alert(`Moved to trash: ${recipeName}`);
    } else {
      setDeleteConfirm(recipeId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  const filteredRecipes = selectedCategory === 'All' 
    ? recipes 
    : recipes.filter(r => r.category === selectedCategory);

  return (
    <div className="relative">
      <form onSubmit={handleSubmit} className="mb-6 md:mb-8">
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-0 sm:justify-center">
          <input 
            type="text" 
            name="url" 
            placeholder="Paste any recipe URL..." 
            className="w-full sm:w-1/2 p-3 border rounded-lg sm:rounded-l-md sm:rounded-r-none text-base bg-background text-foreground"
            disabled={processUrlMutation.isPending}
          />
          <button 
            type="submit" 
            className={`w-full sm:w-auto px-6 py-3 rounded-lg sm:rounded-l-none sm:rounded-r-md transition-colors ${
              processUrlMutation.isPending 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700'
            } text-white font-medium`}
            disabled={processUrlMutation.isPending}
          >
            {processUrlMutation.isPending ? 'Processing...' : 'Import Recipe'}
          </button>
        </div>
        
        {trashCount > 0 && (
          <button
            type="button"
            onClick={() => restoreMutation.mutate()}
            className="w-full sm:w-auto mt-3 sm:mt-0 sm:ml-4 flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white px-4 py-3 sm:py-2 rounded-lg sm:rounded-md transition-colors"
            title={`Restore most recently deleted recipe (${trashCount} in trash)`}
            disabled={restoreMutation.isPending}
          >
            <RotateCcw size={18} />
            Undo Delete ({trashCount})
          </button>
        )}
      </form>

      <div className="mb-6 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0">
        <div className="flex gap-2 sm:flex-wrap sm:justify-center min-w-max sm:min-w-0">
          {CATEGORIES.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-center text-muted-foreground">Loading recipes...</p>}
      {error && <p className="text-center text-destructive">Failed to fetch recipes. Is the backend server running?</p>}
      
      {!isLoading && !error && (
        <>
          <p className="text-center text-muted-foreground mb-4 text-sm md:text-base">
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
                          loading="lazy"
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
                      <CardTitle className="text-xl font-semibold">{recipe.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {recipe.category && (
                        <Badge variant="secondary" className="mb-2">{recipe.category}</Badge>
                      )}
                      {recipe.cuisine && (
                        <Badge variant="outline" className="ml-2 mb-2">{recipe.cuisine}</Badge>
                      )}
                      <p className="text-sm text-muted-foreground mt-2">
                        {recipe.total_time && `${recipe.total_time}`}
                        {recipe.servings && ` | ${recipe.servings} servings`}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
                
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
