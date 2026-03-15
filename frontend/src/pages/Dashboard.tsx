import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/StatusBadge';
import type { Planejamento, Cliente } from '../types';

interface Stats {
  total_clientes: number;
  planejamentos_mes: number;
  aprovados: number;
  em_geracao: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    total_clientes: 0,
    planejamentos_mes: 0,
    aprovados: 0,
    em_geracao: 0,
  });
  const [recentPlanejamentos, setRecentPlanejamentos] = useState<(Planejamento & { cliente_nome?: string })[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [clientesRes, planejamentosRes] = await Promise.all([
          api.get<Cliente[]>('/clientes'),
          api.get<Planejamento[]>('/planejamentos'),
        ]);

        const clientes = clientesRes.data;
        const planejamentos = planejamentosRes.data;

        const now = new Date();
        const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

        setStats({
          total_clientes: clientes.length,
          planejamentos_mes: planejamentos.filter(
            (p) => p.mes_referencia?.startsWith(currentMonth)
          ).length,
          aprovados: planejamentos.filter((p) => p.status === 'aprovado').length,
          em_geracao: planejamentos.filter((p) => p.status === 'em_geracao').length,
        });

        const clienteMap = new Map(clientes.map((c) => [c.id, c.nome_empresa]));
        const recent = planejamentos
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, 10)
          .map((p) => ({ ...p, cliente_nome: clienteMap.get(p.cliente_id) || 'Desconhecido' }));

        setRecentPlanejamentos(recent);
      } catch (err) {
        console.error('Erro ao carregar dashboard:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const statCards = [
    { label: 'Total de Clientes', value: stats.total_clientes, color: 'text-primary', bg: 'bg-primary/5' },
    { label: 'Planejamentos do Mês', value: stats.planejamentos_mes, color: 'text-secondary', bg: 'bg-secondary/5' },
    { label: 'Aprovados', value: stats.aprovados, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Em Geração', value: stats.em_geracao, color: 'text-amber-600', bg: 'bg-amber-50' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-primary">Planejamento de Conteúdo</h1>
          <p className="text-gray-500 mt-1">Gerencie e acompanhe seus planejamentos de conteúdo</p>
        </div>
        <Link to="/novo-planejamento" className="btn-primary flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Novo Planejamento
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => (
          <div key={stat.label} className={`card ${stat.bg}`}>
            <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Recent */}
      <div className="card">
        <h2 className="text-xl font-bold text-primary mb-4">Planejamentos Recentes</h2>

        {recentPlanejamentos.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>Nenhum planejamento encontrado</p>
            <Link to="/novo-planejamento" className="text-accent hover:underline mt-2 inline-block">
              Criar primeiro planejamento
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentPlanejamentos.map((p) => (
              <Link
                key={p.id}
                to={`/planejamentos/${p.id}`}
                className="flex items-center justify-between py-4 hover:bg-gray-50 -mx-6 px-6 transition-colors"
              >
                <div className="flex-1">
                  <p className="font-medium text-primary">{p.cliente_nome}</p>
                  <p className="text-sm text-gray-500">
                    {p.mes_referencia} &middot; {new Date(p.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <StatusBadge status={p.status} size="sm" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
