import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import type { Cliente } from '../types';

export default function ClienteManagement() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClientes();
  }, []);

  async function fetchClientes() {
    try {
      const res = await api.get<Cliente[]>('/clientes');
      setClientes(res.data);
    } catch (err) {
      console.error('Erro ao carregar clientes:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string, nome: string) {
    if (!confirm(`Tem certeza que deseja excluir "${nome}"?`)) return;
    try {
      await api.delete(`/clientes/${id}`);
      setClientes((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error('Erro ao excluir cliente:', err);
      alert('Erro ao excluir cliente. Verifique se não há planejamentos vinculados.');
    }
  }

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
          <h1 className="text-3xl font-bold text-primary">Clientes</h1>
          <p className="text-gray-500 mt-1">Gerencie sua base de clientes</p>
        </div>
        <Link to="/clientes/kick-off" className="btn-primary flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Novo Cliente
        </Link>
      </div>

      {/* Client List */}
      {clientes.length === 0 ? (
        <div className="card text-center py-16">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <p className="text-gray-400 mb-4">Nenhum cliente cadastrado</p>
          <Link to="/clientes/kick-off" className="btn-primary">Cadastrar Primeiro Cliente</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clientes.map((cliente) => (
            <Link
              key={cliente.id}
              to={`/clientes/${cliente.id}/editar`}
              className="card block hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-bold text-primary text-lg">{cliente.nome_empresa}</h3>
                  <p className="text-sm text-gray-500">{cliente.nicho}</p>
                </div>
                <div className="flex gap-1">
                  <span
                    className="p-2 text-gray-400 hover:text-secondary rounded-lg hover:bg-gray-100"
                    title="Editar"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </span>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDelete(cliente.id, cliente.nome_empresa);
                    }}
                    className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100"
                    title="Excluir"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Pilares */}
              {cliente.pilares?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {cliente.pilares.map((p, i) => (
                    <span key={i} className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full font-medium">
                      {p.nome} ({p.percentual}%)
                    </span>
                  ))}
                </div>
              )}

              {/* Tipos */}
              {cliente.tipos_conteudo?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {cliente.tipos_conteudo.map((t, i) => (
                    <span key={i} className="px-2 py-0.5 bg-secondary/10 text-secondary text-xs rounded-full font-medium">
                      {t.tipo.replace(/_/g, ' ')} x{t.quantidade}
                    </span>
                  ))}
                </div>
              )}

              <p className="text-xs text-gray-400 mt-3">
                Cadastrado em {new Date(cliente.created_at).toLocaleDateString('pt-BR')}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
