import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import SearchResults from './pages/SearchResults'
import Nav from './components/nav'

function App() {
  return (
    <Router>
      <Nav />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/search-results" element={<SearchResults />} />
        </Routes>
      </main>
    </Router>
  )
}

export default App
