import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ClienteManagement from './pages/ClienteManagement';
import ClienteForm from './pages/ClienteForm';
import NovoPlanejamento from './pages/NovoPlanejamento';
import PlanejamentoDetail from './pages/PlanejamentoDetail';
import Historico from './pages/Historico';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="clientes" element={<ClienteManagement />} />
        <Route path="clientes/novo" element={<ClienteForm />} />
        <Route path="clientes/:id/editar" element={<ClienteForm />} />
        <Route path="novo-planejamento" element={<NovoPlanejamento />} />
        <Route path="planejamentos/:id" element={<PlanejamentoDetail />} />
        <Route path="historico" element={<Historico />} />
      </Route>
    </Routes>
  );
}

export default App;
