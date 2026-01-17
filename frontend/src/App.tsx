import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import RecipeGallery from './components/RecipeGallery';
import RecipeDetail from './components/RecipeDetail';
import GroceryLists from './components/GroceryLists';
import GroceryListView from './components/GroceryList';
import AdminDashboard from './components/AdminDashboard';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Home, UtensilsCrossed, ShoppingCart, Calendar, Settings, Menu, X, Moon, Sun } from 'lucide-react';

function App() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('darkMode');
      if (saved !== null) return saved === 'true';
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', String(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(prev => !prev);
  
  const isActive = (path: string) => {
    if (path === '/grocery-lists') {
      return location.pathname.startsWith('/grocery-lists');
    }
    return location.pathname === path;
  };

  return (
    <div className="bg-gray-100 dark:bg-gray-900 min-h-screen pb-20 md:pb-0 transition-colors">
      {/* Desktop Header */}
      <header className="bg-white dark:bg-gray-800 shadow sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 md:py-6 flex items-center justify-between">
          <h1 className="text-xl md:text-3xl font-bold text-gray-800 dark:text-gray-100">
            <Link to="/" className="flex items-center gap-2">
              <UtensilsCrossed className="text-blue-500" size={28} />
              <span className="hidden sm:inline">Recipe Manager</span>
              <span className="sm:hidden">Recipes</span>
            </Link>
          </h1>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link 
              to="/" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/') ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Home size={20} />
              Home
            </Link>
            <Link 
              to="/grocery-lists" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/grocery-lists') ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <ShoppingCart size={20} />
              Grocery List
            </Link>
            <Link 
              to="/meal-plan" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/meal-plan') ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Calendar size={20} />
              Meal Plan
            </Link>
            <Link 
              to="/admin" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/admin') ? 'bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <Settings size={20} />
              Admin
            </Link>
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </nav>

          {/* Mobile Menu Button */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              aria-label="Toggle dark mode"
            >
              {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button 
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white dark:bg-gray-800 border-t dark:border-gray-700 px-4 py-2 space-y-1">
            <Link 
              to="/" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Home size={20} />
              Home
            </Link>
            <Link 
              to="/grocery-lists" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <ShoppingCart size={20} />
              Grocery List
            </Link>
            <Link 
              to="/meal-plan" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Calendar size={20} />
              Meal Plan
            </Link>
            <Link 
              to="/admin" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Settings size={20} />
              Admin
            </Link>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-4 md:py-8">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<RecipeGallery />} />
            <Route path="/recipe/:id" element={<RecipeDetail />} />
            <Route path="/grocery-lists" element={<GroceryLists />} />
            <Route path="/grocery-lists/:id" element={<GroceryListView />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </ErrorBoundary>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t dark:border-gray-700 shadow-lg z-50">
        <div className="flex justify-around items-center py-2">
          <Link 
            to="/" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/') ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <Home size={24} />
            <span className="text-xs mt-1">Home</span>
          </Link>
          <Link 
            to="/grocery-lists" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/grocery-lists') ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <ShoppingCart size={24} />
            <span className="text-xs mt-1">Grocery</span>
          </Link>
          <Link 
            to="/meal-plan" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/meal-plan') ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <Calendar size={24} />
            <span className="text-xs mt-1">Plan</span>
          </Link>
          <Link 
            to="/admin" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/admin') ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <Settings size={24} />
            <span className="text-xs mt-1">Admin</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}

export default App;