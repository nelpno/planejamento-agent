import { useState } from 'react';
import type { Conteudo } from '../types';

const tipoBadge: Record<string, { label: string; color: string }> = {
  video_roteiro: { label: 'Vídeo / Roteiro', color: 'bg-purple-100 text-purple-700' },
  arte_estatica: { label: 'Arte Estática', color: 'bg-teal-100 text-teal-700' },
  carrossel: { label: 'Carrossel', color: 'bg-indigo-100 text-indigo-700' },
};

interface ConteudoCardProps {
  conteudo: Conteudo;
}

export default function ConteudoCard({ conteudo }: ConteudoCardProps) {
  const [showVariacoes, setShowVariacoes] = useState(false);

  const badge = tipoBadge[conteudo.tipo] || { label: conteudo.tipo, color: 'bg-gray-100 text-gray-700' };

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
              {badge.label}
            </span>
            {conteudo.framework && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary/10 text-secondary">
                {conteudo.framework}
              </span>
            )}
            {conteudo.pilar && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent">
                {conteudo.pilar}
              </span>
            )}
          </div>
          <h4 className="font-bold text-primary text-lg">{conteudo.titulo}</h4>
        </div>
        <span className="text-xs text-gray-400 font-mono">#{conteudo.ordem}</span>
      </div>

      {/* Body - render content fields */}
      <div className="space-y-3">
        {Object.entries(conteudo.conteudo).map(([key, value]) => (
          <div key={key}>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
              {key.replace(/_/g, ' ')}
            </p>
            <div className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">
              {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
            </div>
          </div>
        ))}
      </div>

      {/* Variações A/B */}
      {conteudo.variacoes_ab && conteudo.variacoes_ab.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowVariacoes(!showVariacoes)}
            className="flex items-center gap-2 text-sm font-medium text-secondary hover:text-accent transition-colors"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showVariacoes ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
            Variações A/B ({conteudo.variacoes_ab.length})
          </button>

          {showVariacoes && (
            <div className="mt-3 space-y-2">
              {conteudo.variacoes_ab.map((variacao, i) => (
                <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-700 mb-1">Variação {i + 1}</p>
                  <p className="text-sm text-gray-700">{variacao.copy_alternativa}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
