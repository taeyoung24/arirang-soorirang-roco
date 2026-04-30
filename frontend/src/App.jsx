import { BrowserRouter, Route, Routes } from 'react-router-dom'
import HomePage from 'src/pages/HomePage'
import IngamePage from 'src/pages/IngamePage'
import LandingPage from 'src/pages/LandingPage'
import SavesPage from 'src/pages/SavesPage'
import SelectionPage from 'src/pages/SelectionPage'

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

export default App;
