import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import api, { API_URL } from '../api/client';
import { connectPlanejamentoWS } from '../api/websocket';
import StatusBadge from '../components/StatusBadge';
import PipelineProgress from '../components/PipelineProgress';
import ConteudoCard from '../components/ConteudoCard';
import FeedbackForm from '../components/FeedbackForm';
import type { Planejamento, Conteudo, PipelineLog, Cliente } from '../types';

export default function PlanejamentoDetail() {
  const { id } = useParams<{ id: string }>();
  const [planejamento, setPlanejamento] = useState<Planejamento | null>(null);
  const [conteudos, setConteudos] = useState<Conteudo[]>([]);
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [pipelineLogs, setPipelineLogs] = useState<PipelineLog[]>([]);
  const [currentAgent, setCurrentAgent] = useState<string>();
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchData();

    return () => {
      wsRef.current?.close();
    };
  }, [id]);

  useEffect(() => {
    if (!id || !planejamento) return;

    if (planejamento.status === 'em_geracao') {
      wsRef.current?.close();
      wsRef.current = connectPlanejamentoWS(id, (data) => {
        if (data.type === 'log') {
          setPipelineLogs((prev) => [...prev, data.log]);
          setCurrentAgent(data.log.agent_name);
        } else if (data.type === 'status_update') {
          setPlanejamento((prev) => prev ? { ...prev, status: data.status } : null);
          if (data.status !== 'em_geracao') {
            wsRef.current?.close();
            fetchData();
          }
        } else if (data.type === 'complete') {
          fetchData();
        }
      });
    }
  }, [id, planejamento?.status]);

  async function fetchData() {
    if (!id) return;
    try {
      const [planRes, conteudosRes] = await Promise.all([
        api.get<Planejamento>(`/planejamentos/${id}`),
        api.get<Conteudo[]>(`/planejamentos/${id}/conteudos`).catch(() => ({ data: [] })),
      ]);

      setPlanejamento(planRes.data);
      setConteudos(conteudosRes.data);

      if (planRes.data.pipeline_logs) {
        const logs = Array.isArray(planRes.data.pipeline_logs)
          ? planRes.data.pipeline_logs
          : Object.values(planRes.data.pipeline_logs).flat();
        setPipelineLogs(logs as PipelineLog[]);
      }

      try {
        const clienteRes = await api.get<Cliente>(`/clientes/${planRes.data.cliente_id}`);
        setCliente(clienteRes.data);
      } catch {}
    } catch (err) {
      console.error('Erro ao carregar planejamento:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleAprovar() {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.post(`/planejamentos/${id}/aprovar`);
      fetchData();
    } catch (err) {
      console.error('Erro ao aprovar:', err);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleFeedback(feedback: string) {
    if (!id) return;
    setActionLoading(true);
    try {
      await api.post(`/planejamentos/${id}/ajustar`, { feedback });
      fetchData();
    } catch (err) {
      console.error('Erro ao enviar feedback:', err);
    } finally {
      setActionLoading(false);
    }
  }

  // Group conteudos by tipo
  const conteudosByTipo = conteudos.reduce<Record<string, Conteudo[]>>((acc, c) => {
    if (!acc[c.tipo]) acc[c.tipo] = [];
    acc[c.tipo].push(c);
    return acc;
  }, {});

  const tipoLabels: Record<string, string> = {
    video_roteiro: 'Videos / Roteiros',
    arte_estatica: 'Artes Estaticas',
    carrossel: 'Carrosseis',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!planejamento) {
    return (
      <div className="card text-center py-16">
        <p className="text-gray-400 mb-4">Planejamento nao encontrado</p>
        <Link to="/" className="text-accent hover:underline">Voltar ao Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link to="/historico" className="text-sm text-gray-500 hover:text-accent flex items-center gap-1 mb-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Voltar
          </Link>
          <h1 className="text-3xl font-bold text-primary">
            {cliente?.nome_empresa || 'Planejamento'}
          </h1>
          <p className="text-gray-500 mt-1">
            {planejamento.mes_referencia} &middot; Criado em {new Date(planejamento.created_at).toLocaleDateString('pt-BR')}
          </p>
        </div>
        <StatusBadge status={planejamento.status} />
      </div>

      {/* Em geração - Pipeline */}
      {planejamento.status === 'em_geracao' && (
        <div className="mb-8">
          <PipelineProgress logs={pipelineLogs} currentAgent={currentAgent} />
        </div>
      )}

      {/* Content sections (revisao, aprovado, ajuste_solicitado) */}
      {['revisao', 'aprovado', 'ajuste_solicitado'].includes(planejamento.status) && (
        <>
          {/* Resumo Estratégico */}
          {planejamento.resumo_estrategico && (
            <div className="card mb-6">
              <h2 className="text-xl font-bold text-primary mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Resumo Estrategico
              </h2>
              <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                {planejamento.resumo_estrategico}
              </div>
            </div>
          )}

          {/* Temas */}
          {planejamento.temas && planejamento.temas.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-bold text-primary mb-4">Temas</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {planejamento.temas.map((tema, i) => (
                  <div key={i} className="card">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2.5 py-0.5 bg-accent/10 text-accent text-xs rounded-full font-medium">
                        {tema.pilar}
                      </span>
                    </div>
                    <h3 className="font-bold text-primary mb-1">{tema.tema}</h3>
                    <p className="text-sm text-gray-600">{tema.justificativa}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Conteúdos por tipo */}
          {Object.entries(conteudosByTipo).map(([tipo, items]) => (
            <div key={tipo} className="mb-6">
              <h2 className="text-xl font-bold text-primary mb-4">
                {tipoLabels[tipo] || tipo}
              </h2>
              <div className="space-y-4">
                {items
                  .sort((a, b) => a.ordem - b.ordem)
                  .map((c) => (
                    <ConteudoCard key={c.id} conteudo={c} />
                  ))}
              </div>
            </div>
          ))}

          {/* Calendário */}
          {planejamento.calendario && planejamento.calendario.length > 0 && (
            <div className="card mb-6">
              <h2 className="text-xl font-bold text-primary mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Calendario de Publicacao
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-semibold text-gray-600">Data</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-600">Tipo</th>
                      <th className="text-left py-3 px-4 font-semibold text-gray-600">Titulo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {planejamento.calendario.map((item, i) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4 font-mono text-gray-700">
                          {new Date(item.data + 'T00:00:00').toLocaleDateString('pt-BR')}
                        </td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 bg-secondary/10 text-secondary text-xs rounded-full font-medium">
                            {item.tipo_conteudo.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-700">{item.titulo}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Pipeline duration */}
          {planejamento.pipeline_duration && (
            <div className="text-sm text-gray-400 mb-6">
              Tempo de geracao: {(planejamento.pipeline_duration / 1000).toFixed(1)}s
            </div>
          )}

          {/* PDF Download */}
          {planejamento.pdf_url && (
            <div className="mb-6">
              <a
                href={`${API_URL}${planejamento.pdf_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary inline-flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Baixar PDF
              </a>
            </div>
          )}

          {/* Actions for revisao */}
          {planejamento.status === 'revisao' && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <button
                  onClick={handleAprovar}
                  disabled={actionLoading}
                  className="bg-green-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Aprovar Planejamento
                </button>
              </div>
              <FeedbackForm onSubmit={handleFeedback} loading={actionLoading} />
            </div>
          )}
        </>
      )}

      {/* Failed */}
      {planejamento.status === 'failed' && (
        <div className="card border-red-200 bg-red-50/30">
          <h3 className="font-bold text-red-700 mb-2 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Erro na Geracao
          </h3>
          <p className="text-sm text-red-600">
            Ocorreu um erro durante a geracao do planejamento. Tente novamente ou entre em contato com o suporte.
          </p>
          {pipelineLogs.length > 0 && (
            <div className="mt-4">
              <PipelineProgress logs={pipelineLogs} />
            </div>
          )}
        </div>
      )}

      {/* Rascunho */}
      {planejamento.status === 'rascunho' && (
        <div className="card text-center py-12 text-gray-400">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <p>Este planejamento esta em rascunho e ainda nao foi gerado.</p>
        </div>
      )}
    </div>
  );
}
