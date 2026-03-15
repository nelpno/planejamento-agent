import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { API_URL } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { Planejamento, Cliente } from '../types';

export default function Historico() {
  const [planejamentos, setPlanejamentos] = useState<(Planejamento & { cliente_nome?: string })[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [filtroCliente, setFiltroCliente] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [planRes, clienteRes] = await Promise.all([
          api.get<Planejamento[]>('/planejamentos'),
          api.get<Cliente[]>('/clientes'),
        ]);

        setClientes(clienteRes.data);

        const clienteMap = new Map(clienteRes.data.map((c) => [c.id, c.nome_empresa]));
        const enriched = planRes.data
          .map((p) => ({ ...p, cliente_nome: clienteMap.get(p.cliente_id) || 'Desconhecido' }))
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

        setPlanejamentos(enriched);
      } catch (err) {
        console.error('Erro ao carregar historico:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const filtered = filtroCliente
    ? planejamentos.filter((p) => p.cliente_id === filtroCliente)
    : planejamentos;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Historico</h1>
          <p className="text-gray-500 mt-1">Todos os planejamentos gerados</p>
        </div>
        <Link to="/novo-planejamento" className="btn-primary flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Novo Planejamento
        </Link>
      </div>

      {/* Filtro */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="text-sm font-semibold text-gray-700 whitespace-nowrap">Filtrar por cliente:</label>
          <select
            className="input-field max-w-xs"
            value={filtroCliente}
            onChange={(e) => setFiltroCliente(e.target.value)}
          >
            <option value="">Todos os clientes</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>{c.nome_empresa}</option>
            ))}
          </select>
          {filtroCliente && (
            <button
              onClick={() => setFiltroCliente('')}
              className="text-sm text-accent hover:underline"
            >
              Limpar filtro
            </button>
          )}
        </div>
      </div>

      {/* Lista */}
      {filtered.length === 0 ? (
        <div className="card text-center py-16">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-400">Nenhum planejamento encontrado</p>
        </div>
      ) : (
        <div className="card">
          <div className="divide-y divide-gray-100">
            {filtered.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-4 py-4 hover:bg-gray-50 -mx-6 px-6 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/planejamentos/${p.id}`}
                    className="font-medium text-primary hover:text-accent transition-colors"
                  >
                    {p.cliente_nome}
                  </Link>
                  <p className="text-sm text-gray-500">
                    {p.mes_referencia} &middot; {new Date(p.created_at).toLocaleDateString('pt-BR')}
                    {p.pipeline_duration && (
                      <> &middot; {p.pipeline_duration.toFixed(0)}s</>
                    )}
                  </p>
                </div>

                <StatusBadge status={p.status} size="sm" />

                <div className="flex items-center gap-2">
                  {p.pdf_url && (
                    <a
                      href={`${API_URL}${p.pdf_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 text-gray-400 hover:text-secondary rounded-lg hover:bg-gray-100"
                      title="Baixar PDF"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </a>
                  )}
                  <Link
                    to={`/planejamentos/${p.id}`}
                    className="p-2 text-gray-400 hover:text-accent rounded-lg hover:bg-gray-100"
                    title="Ver detalhes"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
