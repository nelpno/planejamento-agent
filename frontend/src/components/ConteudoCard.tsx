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

      {/* Body - render content by type */}
      <div className="space-y-3">
        {conteudo.tipo.includes('carrossel') ? (
          <>
            {/* Carrossel: render each slide with full content */}
            {conteudo.conteudo.capa && (
              <div className="bg-accent/5 border border-accent/20 rounded-lg p-4">
                <p className="text-xs font-bold text-accent uppercase mb-1">Capa</p>
                <p className="font-bold text-primary">
                  {typeof conteudo.conteudo.capa === 'string' ? conteudo.conteudo.capa : conteudo.conteudo.capa?.titulo || ''}
                </p>
                {typeof conteudo.conteudo.capa === 'object' && conteudo.conteudo.capa?.subtitulo && (
                  <p className="text-sm text-gray-600 mt-1">{conteudo.conteudo.capa.subtitulo}</p>
                )}
              </div>
            )}
            {conteudo.conteudo.slides && Array.isArray(conteudo.conteudo.slides) && (
              <div className="space-y-2">
                {conteudo.conteudo.slides.map((slide: any, i: number) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-4 border-l-4 border-secondary/40">
                    <p className="text-xs font-bold text-secondary mb-1">
                      Slide {i + 1}
                      {i === 0 && !conteudo.conteudo.capa ? ' (Capa)' : ''}
                      {i === conteudo.conteudo.slides.length - 1 ? ' (CTA)' : ''}
                    </p>
                    {slide.titulo && <p className="font-semibold text-primary text-sm">{slide.titulo}</p>}
                    {(slide.texto || slide.conteudo) && (
                      <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{slide.texto || slide.conteudo}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
            {conteudo.conteudo.cta_final && (
              <div className="bg-accent/10 rounded-lg p-3 border border-accent/20">
                <p className="text-xs font-bold text-accent uppercase mb-1">CTA Final</p>
                <p className="text-sm font-medium text-primary">{conteudo.conteudo.cta_final}</p>
              </div>
            )}
            {conteudo.conteudo.copy_legenda && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Legenda</p>
                <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">{conteudo.conteudo.copy_legenda}</p>
              </div>
            )}
            {conteudo.conteudo.hashtags && (
              <div className="flex flex-wrap gap-1">
                {(Array.isArray(conteudo.conteudo.hashtags) ? conteudo.conteudo.hashtags : []).map((h: string, i: number) => (
                  <span key={i} className="text-xs text-secondary font-medium">{h}</span>
                ))}
              </div>
            )}
          </>
        ) : conteudo.tipo.includes('video') ? (
          <>
            {/* Vídeo: render gancho, desenvolvimento, CTA with visual hierarchy */}
            {conteudo.conteudo.gancho && (
              <div className="bg-amber-50 border-l-4 border-amber-400 rounded-r-lg p-4">
                <p className="text-xs font-bold text-amber-700 uppercase mb-1">Gancho (0-3s)</p>
                <p className="text-sm text-gray-800 font-medium whitespace-pre-wrap">{conteudo.conteudo.gancho}</p>
              </div>
            )}
            {conteudo.conteudo.desenvolvimento && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Desenvolvimento</p>
                <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">{conteudo.conteudo.desenvolvimento}</p>
              </div>
            )}
            {(conteudo.conteudo.cta || conteudo.conteudo.cta_final) && (
              <div className="bg-accent/10 border-l-4 border-accent rounded-r-lg p-4">
                <p className="text-xs font-bold text-accent uppercase mb-1">CTA</p>
                <p className="text-sm font-medium text-primary whitespace-pre-wrap">{conteudo.conteudo.cta || conteudo.conteudo.cta_final}</p>
              </div>
            )}
            {conteudo.conteudo.duracao_estimada && (
              <p className="text-xs text-gray-400">Duração: {conteudo.conteudo.duracao_estimada}</p>
            )}
          </>
        ) : (
          <>
            {/* Arte estática ou genérico */}
            {Object.entries(conteudo.conteudo).map(([key, value]) => {
              if (key === 'hashtags' && Array.isArray(value)) {
                return (
                  <div key={key} className="flex flex-wrap gap-1">
                    {value.map((h: string, i: number) => (
                      <span key={i} className="text-xs text-secondary font-medium">{h}</span>
                    ))}
                  </div>
                );
              }
              if (key === 'cta_botao' || key === 'cta') {
                return (
                  <div key={key} className="bg-accent/10 border-l-4 border-accent rounded-r-lg p-3">
                    <p className="text-xs font-bold text-accent uppercase mb-1">CTA Botão</p>
                    <p className="text-sm font-medium text-primary">{String(value)}</p>
                  </div>
                );
              }
              return (
                <div key={key}>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                    {key.replaceAll('_', ' ')}
                  </p>
                  <div className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">
                    {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                  </div>
                </div>
              );
            })}
          </>
        )}
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
