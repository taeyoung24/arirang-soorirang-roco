import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import HomePage from './pages/HomePage'
import SelectionPage from './pages/SelectionPage'
import IngamePage from './pages/IngamePage'
import SavesPage from './pages/SavesPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/selection" element={<SelectionPage />} />
        <Route path="/ingame" element={<IngamePage />} />
        <Route path="/saves" element={<SavesPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
