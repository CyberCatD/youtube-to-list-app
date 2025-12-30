// src/components/RecipeGallery.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import type { Recipe } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const RecipeGallery = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  useEffect(() => {
    fetchRecipes();
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const urlInput = event.currentTarget.elements.namedItem('url') as HTMLInputElement;
    const url = urlInput.value;
    
    try {
      await axios.post('/api/v1/youtube/process-youtube-url', { youtube_url: url });
      urlInput.value = '';
      fetchRecipes(); // Refresh the gallery
    } catch (err) {
      alert('Failed to process URL. See console for details.');
      console.error(err);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-8 flex justify-center">
        <input type="text" name="url" placeholder="Enter YouTube URL..." className="w-1/2 p-2 border rounded-l-md" />
        <button type="submit" className="bg-blue-500 text-white p-2 rounded-r-md hover:bg-blue-600">Process</button>
      </form>

      {loading && <p className="text-center text-gray-500">Loading recipes...</p>}
      {error && <p className="text-center text-red-500">{error}</p>}
      
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {recipes.map((recipe) => (
            <Link to={`/recipe/${recipe.id}`} key={recipe.id} className="block">
              <Card className="hover:shadow-xl transition-shadow duration-300" style={{ backgroundColor: recipe.card_color || '#EAEAEA' }}>
                <CardHeader>
                  <CardTitle className="text-xl font-semibold text-gray-800">{recipe.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600">{recipe.category}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecipeGallery;
