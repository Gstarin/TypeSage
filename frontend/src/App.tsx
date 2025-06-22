import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Analyzer from './pages/Analyzer'
import Visualization from './pages/Visualization'
import Memory from './pages/Memory'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyzer" element={<Analyzer />} />
        <Route path="/visualization/:codeHash" element={<Visualization />} />
        <Route path="/memory" element={<Memory />} />
      </Routes>
    </Layout>
  )
}

export default App 