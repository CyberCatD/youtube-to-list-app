import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useState } from 'react';
import RecipeGallery from './components/RecipeGallery';
import RecipeDetail from './components/RecipeDetail';
import { Home, UtensilsCrossed, ShoppingCart, Calendar, User, Menu, X } from 'lucide-react';

function App() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="bg-gray-100 min-h-screen pb-20 md:pb-0">
      {/* Desktop Header */}
      <header className="bg-white shadow sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 md:py-6 flex items-center justify-between">
          <h1 className="text-xl md:text-3xl font-bold text-gray-800">
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
                isActive('/') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Home size={20} />
              Home
            </Link>
            <Link 
              to="/grocery-list" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/grocery-list') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <ShoppingCart size={20} />
              Grocery List
            </Link>
            <Link 
              to="/meal-plan" 
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive('/meal-plan') ? 'bg-blue-100 text-blue-600' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Calendar size={20} />
              Meal Plan
            </Link>
          </nav>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden p-2 rounded-lg hover:bg-gray-100"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t px-4 py-2 space-y-1">
            <Link 
              to="/" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
            >
              <Home size={20} />
              Home
            </Link>
            <Link 
              to="/grocery-list" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
            >
              <ShoppingCart size={20} />
              Grocery List
            </Link>
            <Link 
              to="/meal-plan" 
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-3 rounded-lg text-gray-700 hover:bg-gray-100"
            >
              <Calendar size={20} />
              Meal Plan
            </Link>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-4 md:py-8">
        <Routes>
          <Route path="/" element={<RecipeGallery />} />
          <Route path="/recipe/:id" element={<RecipeDetail />} />
        </Routes>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg z-50">
        <div className="flex justify-around items-center py-2">
          <Link 
            to="/" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/') ? 'text-blue-600' : 'text-gray-500'
            }`}
          >
            <Home size={24} />
            <span className="text-xs mt-1">Home</span>
          </Link>
          <Link 
            to="/grocery-list" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/grocery-list') ? 'text-blue-600' : 'text-gray-500'
            }`}
          >
            <ShoppingCart size={24} />
            <span className="text-xs mt-1">Grocery</span>
          </Link>
          <Link 
            to="/meal-plan" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/meal-plan') ? 'text-blue-600' : 'text-gray-500'
            }`}
          >
            <Calendar size={24} />
            <span className="text-xs mt-1">Plan</span>
          </Link>
          <Link 
            to="/profile" 
            className={`flex flex-col items-center px-4 py-2 rounded-lg ${
              isActive('/profile') ? 'text-blue-600' : 'text-gray-500'
            }`}
          >
            <User size={24} />
            <span className="text-xs mt-1">Profile</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}

export default App;