import { Routes, Route, Link } from 'react-router-dom';
import RecipeGallery from './components/RecipeGallery';
import RecipeDetail from './components/RecipeDetail';

function App() {
  return (
    <div className="bg-gray-100 min-h-screen">
      <header className="bg-white shadow">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-800">
            <Link to="/">YouTube Recipe Collector</Link>
          </h1>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<RecipeGallery />} />
          <Route path="/recipe/:id" element={<RecipeDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;