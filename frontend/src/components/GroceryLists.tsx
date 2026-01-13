import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { GroceryList } from '../types';
import { Card, CardContent } from './ui/card';
import { ShoppingCart, Plus, ChevronRight, Trash2 } from 'lucide-react';

function GroceryLists() {
  const navigate = useNavigate();
  const [lists, setLists] = useState<GroceryList[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchLists();
  }, []);

  const fetchLists = async () => {
    try {
      const response = await axios.get('/api/v1/grocery-lists/');
      setLists(response.data);
    } catch (err) {
      console.error('Failed to fetch grocery lists:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEmpty = async () => {
    setCreating(true);
    try {
      const response = await axios.post('/api/v1/grocery-lists/', {
        name: `Grocery List ${new Date().toLocaleDateString()}`,
        recipe_ids: [],
      });
      navigate(`/grocery-lists/${response.data.id}`);
    } catch (err) {
      console.error('Failed to create list:', err);
      alert('Failed to create grocery list');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, listId: number) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm('Delete this grocery list?')) return;

    try {
      await axios.delete(`/api/v1/grocery-lists/${listId}`);
      setLists(lists.filter(l => l.id !== listId));
    } catch (err) {
      console.error('Failed to delete list:', err);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Grocery Lists</h1>
        <button
          onClick={handleCreateEmpty}
          disabled={creating}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <Plus size={20} />
          <span>New List</span>
        </button>
      </div>

      {lists.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <ShoppingCart size={48} className="mx-auto text-gray-300 mb-4" />
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No grocery lists yet</h2>
            <p className="text-gray-500 mb-4">
              Create a grocery list from your recipes to get started.
            </p>
            <Link
              to="/"
              className="text-blue-600 hover:underline"
            >
              Browse recipes
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {lists.map(list => {
            const checkedCount = list.items.filter(i => i.is_checked).length;
            const progress = list.items.length > 0
              ? Math.round((checkedCount / list.items.length) * 100)
              : 0;

            return (
              <Link
                key={list.id}
                to={`/grocery-lists/${list.id}`}
                className="block"
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{list.name}</h3>
                        <p className="text-sm text-gray-500">
                          {list.items.length} items • {list.recipes.length} recipes
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Updated {formatDate(list.updated_at)}
                        </p>
                        
                        {list.items.length > 0 && (
                          <div className="mt-2">
                            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden w-32">
                              <div
                                className="h-full bg-green-500 transition-all"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => handleDelete(e, list.id)}
                          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                        >
                          <Trash2 size={18} />
                        </button>
                        <ChevronRight size={20} className="text-gray-400" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default GroceryLists;
