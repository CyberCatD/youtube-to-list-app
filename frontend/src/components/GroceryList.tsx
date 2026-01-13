import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { GroceryList as GroceryListType, GroceryListItem } from '../types';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Check, ChevronLeft, Share2, Trash2, X } from 'lucide-react';

const CATEGORY_ORDER = [
  'Produce',
  'Dairy',
  'Eggs',
  'Meat & Seafood',
  'Bakery & Bread',
  'Pantry',
  'Frozen',
  'Beverages',
  'Other',
];

function GroceryListView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [groceryList, setGroceryList] = useState<GroceryListType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchGroceryList = async () => {
      try {
        const response = await axios.get(`/api/v1/grocery-lists/${id}`);
        setGroceryList(response.data);
      } catch (err) {
        console.error('Failed to fetch grocery list:', err);
        setError('Failed to load grocery list');
      } finally {
        setLoading(false);
      }
    };

    fetchGroceryList();
  }, [id]);

  const handleToggleItem = async (itemId: number) => {
    if (!groceryList) return;

    try {
      const response = await axios.patch(`/api/v1/grocery-lists/items/${itemId}/toggle`);
      const updatedItem: GroceryListItem = response.data;
      
      setGroceryList({
        ...groceryList,
        items: groceryList.items.map(item =>
          item.id === itemId ? updatedItem : item
        ),
      });
    } catch (err) {
      console.error('Failed to toggle item:', err);
    }
  };

  const handleRemoveRecipe = async (recipeId: number) => {
    if (!groceryList) return;

    try {
      const response = await axios.delete(`/api/v1/grocery-lists/${groceryList.id}/recipes/${recipeId}`);
      setGroceryList(response.data);
    } catch (err) {
      console.error('Failed to remove recipe:', err);
    }
  };

  const handleDeleteList = async () => {
    if (!groceryList) return;
    
    if (!confirm('Are you sure you want to delete this grocery list?')) return;

    try {
      await axios.delete(`/api/v1/grocery-lists/${groceryList.id}`);
      navigate('/grocery-lists');
    } catch (err) {
      console.error('Failed to delete list:', err);
    }
  };

  const formatItemForShare = (item: GroceryListItem): string => {
    if (item.retail_package) {
      const count = item.retail_package_count && item.retail_package_count > 1 
        ? `${item.retail_package_count}x ` 
        : '';
      const exact = item.exact_amount ? ` (${item.exact_amount})` : '';
      return `${count}${item.retail_package} ${item.ingredient_name}${exact}`;
    } else if (item.exact_amount) {
      return `${item.exact_amount} ${item.ingredient_name}`;
    } else if (item.quantity) {
      return `${item.quantity} ${item.unit || ''} ${item.ingredient_name}`.trim();
    }
    return item.ingredient_name;
  };

  const handleShare = async () => {
    if (!groceryList) return;

    const checkedItems = groceryList.items.filter(i => i.is_checked);
    const uncheckedItems = groceryList.items.filter(i => !i.is_checked);

    let text = `${groceryList.name}\n\n`;
    
    if (uncheckedItems.length > 0) {
      text += 'To Buy:\n';
      uncheckedItems.forEach(item => {
        text += `[ ] ${formatItemForShare(item)}\n`;
      });
    }

    if (checkedItems.length > 0) {
      text += '\nAlready Have:\n';
      checkedItems.forEach(item => {
        text += `[x] ${formatItemForShare(item)}\n`;
      });
    }

    if (navigator.share) {
      try {
        await navigator.share({ title: groceryList.name, text });
      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          await navigator.clipboard.writeText(text);
          alert('Copied to clipboard!');
        }
      }
    } else {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard!');
    }
  };

  const itemsByCategory = useMemo(() => {
    if (!groceryList) return {};
    
    const grouped: Record<string, GroceryListItem[]> = {};
    
    groceryList.items.forEach(item => {
      const category = item.category || 'Other';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(item);
    });

    Object.keys(grouped).forEach(category => {
      grouped[category].sort((a, b) => {
        if (a.is_checked !== b.is_checked) {
          return a.is_checked ? 1 : -1;
        }
        return a.ingredient_name.localeCompare(b.ingredient_name);
      });
    });

    return grouped;
  }, [groceryList]);

  const sortedCategories = useMemo(() => {
    return CATEGORY_ORDER.filter(cat => itemsByCategory[cat]?.length > 0);
  }, [itemsByCategory]);

  const progress = useMemo(() => {
    if (!groceryList || groceryList.items.length === 0) return 0;
    const checked = groceryList.items.filter(i => i.is_checked).length;
    return Math.round((checked / groceryList.items.length) * 100);
  }, [groceryList]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !groceryList) {
    return (
      <div className="max-w-2xl mx-auto p-4">
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-red-500">{error || 'Grocery list not found'}</p>
            <Link to="/grocery-lists" className="text-blue-600 hover:underline mt-2 inline-block">
              Back to lists
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => navigate('/grocery-lists')}
          className="flex items-center gap-1 text-gray-600 hover:text-gray-800"
        >
          <ChevronLeft size={20} />
          <span>Back</span>
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={handleShare}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
            title="Share list"
          >
            <Share2 size={20} />
          </button>
          <button
            onClick={handleDeleteList}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
            title="Delete list"
          >
            <Trash2 size={20} />
          </button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-2xl">{groceryList.name}</CardTitle>
          <p className="text-sm text-gray-500">
            {groceryList.items.length} items from {groceryList.recipes.length} recipe(s)
          </p>
          
          <div className="mt-3">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-4">
          {groceryList.recipes.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Recipes in this list:</h3>
              <div className="flex flex-wrap gap-2">
                {groceryList.recipes.map(recipe => (
                  <div
                    key={recipe.id}
                    className="flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1"
                  >
                    <Link
                      to={`/recipe/${recipe.id}`}
                      className="text-sm text-gray-700 hover:text-blue-600"
                    >
                      {recipe.name}
                    </Link>
                    <button
                      onClick={() => handleRemoveRecipe(recipe.id)}
                      className="text-gray-400 hover:text-red-500"
                      title="Remove recipe"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-6">
            {sortedCategories.map(category => (
              <div key={category}>
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  {category}
                </h3>
                <div className="space-y-1">
                  {itemsByCategory[category].map(item => (
                    <div
                      key={item.id}
                      onClick={() => handleToggleItem(item.id)}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                        item.is_checked
                          ? 'bg-gray-50 text-gray-400'
                          : 'bg-white hover:bg-gray-50'
                      }`}
                    >
                      <div
                        className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                          item.is_checked
                            ? 'bg-green-500 border-green-500'
                            : 'border-gray-300'
                        }`}
                      >
                        {item.is_checked && <Check size={14} className="text-white" />}
                      </div>
                      <div className="flex-1">
                        <span
                          className={`${
                            item.is_checked ? 'line-through' : ''
                          }`}
                        >
                          {item.retail_package ? (
                            <>
                              <span className="font-medium">
                                {item.retail_package_count && item.retail_package_count > 1 
                                  ? `${item.retail_package_count}x ` 
                                  : ''
                                }
                                {item.retail_package}
                              </span>
                              {' '}{item.ingredient_name}
                              {item.exact_amount && (
                                <span className="text-gray-500 text-sm ml-1">
                                  ({item.exact_amount})
                                </span>
                              )}
                            </>
                          ) : (
                            <>
                              {item.exact_amount ? (
                                <span className="font-medium">{item.exact_amount} </span>
                              ) : item.quantity !== null && item.quantity > 0 ? (
                                <span className="font-medium">
                                  {item.quantity} {item.unit}{' '}
                                </span>
                              ) : null}
                              {item.ingredient_name}
                            </>
                          )}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default GroceryListView;
