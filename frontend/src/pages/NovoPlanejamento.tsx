import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import type { Cliente } from '../types';

export default function NovoPlanejamento() {
  const navigate = useNavigate();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [clienteId, setClienteId] = useState('');
  const [mesReferencia, setMesReferencia] = useState('');
  const [inputsExtras, setInputsExtras] = useState('');
  const [produtosPromover, setProdutosPromover] = useState('');
  const [referenciasAnteriores, setReferenciasAnteriores] = useState('');
  const [feedbackReuniao, setFeedbackReuniao] = useState('');
  const [tiposConteudo, setTiposConteudo] = useState<Array<{ tipo: string; quantidade: number }>>([]);
  const [foco, setFoco] = useState<string | null>(null);
  const [destinoConversao, setDestinoConversao] = useState<string | null>(null);
  const [tipoConteudoUso, setTipoConteudoUso] = useState<string | null>(null);
  const [plataformas, setPlataformas] = useState<string[]>([]);

  const selectedCliente = clientes.find((c) => c.id === clienteId);

  useEffect(() => {
    api.get<Cliente[]>('/clientes')
      .then((res) => setClientes(res.data))
      .catch((err) => console.error('Erro ao carregar clientes:', err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Set default month to current
    const now = new Date();
    setMesReferencia(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
  }, []);

  // Pre-preencher defaults do cliente selecionado
  useEffect(() => {
    if (selectedCliente) {
      setFoco(selectedCliente.foco_padrao || null);
      setDestinoConversao(selectedCliente.destino_padrao || null);
      setTipoConteudoUso(selectedCliente.tipo_uso_padrao || null);
      setPlataformas(selectedCliente.plataformas_padrao || []);
      if (selectedCliente.tipos_conteudo?.length) {
        setTiposConteudo(
          selectedCliente.tipos_conteudo.map((t) => ({ tipo: t.tipo, quantidade: t.quantidade }))
        );
      } else {
        setTiposConteudo([]);
      }
    }
  }, [clienteId, selectedCliente]);

  function updateTipoQuantidade(index: number, quantidade: number) {
    const updated = [...tiposConteudo];
    updated[index] = { ...updated[index], quantidade };
    setTiposConteudo(updated);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!clienteId || !mesReferencia) return;

    setSubmitting(true);
    try {
      const res = await api.post('/planejamentos', {
        cliente_id: clienteId,
        mes_referencia: mesReferencia,
        produtos_promover: produtosPromover || null,
        referencias_anteriores: referenciasAnteriores || null,
        feedback_reuniao: feedbackReuniao || null,
        inputs_extras: inputsExtras || null,
        tipos_conteudo_override: tiposConteudo.length > 0 ? tiposConteudo : undefined,
        foco: foco || null,
        destino_conversao: destinoConversao || null,
        tipo_conteudo_uso: tipoConteudoUso || null,
        plataformas: plataformas.length > 0 ? plataformas : null,
      });

      navigate(`/planejamentos/${res.data.id}`);
    } catch (err) {
      console.error('Erro ao criar planejamento:', err);
      alert('Erro ao criar planejamento. Verifique os dados e tente novamente.');
    } finally {
      setSubmitting(false);
    }
  }

  const tipoLabels: Record<string, string> = {
    video_roteiro: 'Video / Roteiro',
    arte_estatica: 'Arte Estatica',
    carrossel: 'Carrossel',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">Novo Planejamento</h1>
        <p className="text-gray-500 mt-1">Preencha os dados para gerar um novo planejamento de conteudo</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1/4: Cliente + Mes */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-accent text-white rounded-full flex items-center justify-center font-bold text-sm">1</span>
            <h2 className="text-lg font-bold text-primary">Cliente + Mes</h2>
            <span className="text-xs text-gray-400 ml-auto">1/4</span>
          </div>

          {clientes.length === 0 ? (
            <div className="text-center py-6 text-gray-400">
              <p>Nenhum cliente cadastrado.</p>
              <button
                type="button"
                onClick={() => navigate('/clientes/novo')}
                className="text-accent hover:underline mt-1"
              >
                Cadastrar cliente primeiro
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label htmlFor="cliente-select" className="block text-sm font-semibold text-gray-700 mb-1">
                  Cliente
                </label>
                <select
                  id="cliente-select"
                  className="input-field"
                  value={clienteId}
                  onChange={(e) => setClienteId(e.target.value)}
                  required
                >
                  <option value="">Selecione um cliente...</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.nome_empresa} - {c.nicho}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="mes-ref" className="block text-sm font-semibold text-gray-700 mb-1">
                  Mes de Referencia
                </label>
                <input
                  id="mes-ref"
                  type="month"
                  className="input-field"
                  value={mesReferencia}
                  onChange={(e) => setMesReferencia(e.target.value)}
                  required
                />
              </div>
            </div>
          )}
        </div>

        {/* Step 2/4: Direcionamento do Mes */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-accent text-white rounded-full flex items-center justify-center font-bold text-sm">2</span>
            <h2 className="text-lg font-bold text-primary">Direcionamento do Mes</h2>
            <span className="text-xs text-gray-400 ml-auto">2/4</span>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Defina o que o cliente quer fazer este mes. Esses inputs direcionam TODO o conteudo gerado.
          </p>
          <div className="space-y-4">
            <div>
              <label htmlFor="produtos-promover" className="block text-sm font-semibold text-gray-700 mb-1">
                O que o cliente quer vender/promover este mes?
              </label>
              <textarea
                id="produtos-promover"
                className="input-field min-h-[100px]"
                value={produtosPromover}
                onChange={(e) => setProdutosPromover(e.target.value)}
                placeholder="Ex: Pacote de ferias com 20% de desconto, novo servico de consultoria, campanha do Dia das Maes..."
              />
            </div>
            <div>
              <label htmlFor="referencias-anteriores" className="block text-sm font-semibold text-gray-700 mb-1">
                Referencias — o que performou bem no mes anterior?
              </label>
              <textarea
                id="referencias-anteriores"
                className="input-field min-h-[80px]"
                value={referenciasAnteriores}
                onChange={(e) => setReferenciasAnteriores(e.target.value)}
                placeholder="Ex: Video sobre horas extras teve 45K views, carrossel de direitos trabalhistas teve 2K saves..."
              />
            </div>
            <div>
              <label htmlFor="feedback-reuniao" className="block text-sm font-semibold text-gray-700 mb-1">
                Feedback/anotacoes da reuniao mensal
              </label>
              <textarea
                id="feedback-reuniao"
                className="input-field min-h-[100px]"
                value={feedbackReuniao}
                onChange={(e) => setFeedbackReuniao(e.target.value)}
                placeholder="Cole aqui a transcricao da reuniao ou suas anotacoes. Ex: Cliente quer focar em gestantes este mes, pediu para nao falar de acidente de trabalho..."
              />
            </div>
            <div>
              <label htmlFor="observacoes" className="block text-sm font-semibold text-gray-700 mb-1">
                Observacoes adicionais <span className="text-gray-400 font-normal">(opcional)</span>
              </label>
              <textarea
                id="observacoes"
                className="input-field min-h-[60px]"
                value={inputsExtras}
                onChange={(e) => setInputsExtras(e.target.value)}
                placeholder="Qualquer observacao adicional para o planejamento..."
              />
            </div>
          </div>
        </div>

        {/* Step 3/4: Configuracao */}
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <span className="w-8 h-8 bg-accent text-white rounded-full flex items-center justify-center font-bold text-sm">3</span>
            <h2 className="text-lg font-bold text-primary">Configuracao</h2>
            <span className="text-xs text-gray-400 ml-auto">3/4</span>
          </div>
          {selectedCliente && (selectedCliente.foco_padrao || selectedCliente.destino_padrao || selectedCliente.tipo_uso_padrao || selectedCliente.plataformas_padrao) && (
            <p className="text-xs text-gray-400 italic mb-4">
              Pre-preenchido com padrao do cliente. Altere se necessario.
            </p>
          )}

          {/* Foco do Mes */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Foco do Mes</h3>
            <p className="text-xs text-gray-500 mb-3">Qual o objetivo principal do conteudo deste mes?</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { id: 'geracao_leads', label: 'Geracao de Leads', descricao: 'Captar contatos qualificados', icon: '👥' },
                { id: 'vendas_ecommerce', label: 'Vendas / E-commerce', descricao: 'Direcionar para compra online', icon: '🛒' },
                { id: 'crescimento_organico', label: 'Crescimento Organico', descricao: 'Aumentar seguidores e engajamento', icon: '📈' },
                { id: 'branding', label: 'Branding / Posicionamento', descricao: 'Fortalecer marca e autoridade', icon: '🏆' },
                { id: 'lancamento', label: 'Lancamento', descricao: 'Lancar produto, servico ou evento', icon: '🚀' },
                { id: 'retencao', label: 'Retencao / Relacionamento', descricao: 'Fidelizar clientes existentes', icon: '❤️' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setFoco(foco === item.id ? null : item.id)}
                  className={`text-left p-4 rounded-lg border-2 transition-all ${
                    foco === item.id
                      ? 'border-accent bg-accent/5 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{item.icon}</span>
                    <span className="font-semibold text-sm text-primary">{item.label}</span>
                  </div>
                  <p className="text-xs text-gray-500">{item.descricao}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Destino da Conversao */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Destino da Conversao</h3>
            <p className="text-xs text-gray-500 mb-3">Para onde os CTAs devem direcionar o publico?</p>
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'whatsapp', label: 'WhatsApp' },
                { id: 'site', label: 'Site / Landing Page' },
                { id: 'dm_instagram', label: 'DM Instagram' },
                { id: 'loja_online', label: 'Loja Online' },
                { id: 'agendamento', label: 'Agendamento' },
                { id: 'telefone', label: 'Telefone' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setDestinoConversao(destinoConversao === item.id ? null : item.id)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    destinoConversao === item.id
                      ? 'bg-accent text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tipo de Conteudo (Uso) */}
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Tipo de Conteudo</h3>
            <p className="text-xs text-gray-500 mb-3">O conteudo sera para uso organico, pago ou ambos?</p>
            <div className="flex gap-2">
              {[
                { id: 'organico', label: 'Organico' },
                { id: 'pago', label: 'Trafego Pago (Ads)' },
                { id: 'ambos', label: 'Ambos' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTipoConteudoUso(tipoConteudoUso === item.id ? null : item.id)}
                  className={`flex-1 px-4 py-3 rounded-lg text-sm font-medium transition-all border-2 ${
                    tipoConteudoUso === item.id
                      ? 'bg-accent text-white border-accent shadow-sm'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {/* Plataformas */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Plataformas</h3>
            <p className="text-xs text-gray-500 mb-3">Em quais plataformas o conteudo sera publicado? (selecao multipla)</p>
            <div className="flex flex-wrap gap-2">
              {[
                { id: 'instagram', label: 'Instagram' },
                { id: 'tiktok', label: 'TikTok' },
                { id: 'youtube', label: 'YouTube' },
                { id: 'linkedin', label: 'LinkedIn' },
                { id: 'facebook', label: 'Facebook' },
              ].map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() =>
                    setPlataformas((prev) =>
                      prev.includes(item.id) ? prev.filter((p) => p !== item.id) : [...prev, item.id]
                    )
                  }
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    plataformas.includes(item.id)
                      ? 'bg-accent text-white shadow-sm'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Step 4/4: Tipos de Conteudo */}
        {selectedCliente && tiposConteudo.length > 0 && (
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <span className="w-8 h-8 bg-accent text-white rounded-full flex items-center justify-center font-bold text-sm">4</span>
              <h2 className="text-lg font-bold text-primary">Tipos de Conteudo</h2>
              <span className="text-xs text-gray-400 ml-auto">4/4</span>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Pre-preenchido do cadastro do cliente. Ajuste as quantidades se necessario.
            </p>
            <div className="space-y-3">
              {tiposConteudo.map((tipo, i) => (
                <div key={i} className="flex items-center gap-4 bg-gray-50 rounded-lg p-3">
                  <span className="flex-1 font-medium text-gray-700">
                    {tipoLabels[tipo.tipo] || tipo.tipo}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => updateTipoQuantidade(i, Math.max(0, tipo.quantidade - 1))}
                      className="w-8 h-8 bg-white border rounded-lg flex items-center justify-center hover:bg-gray-100"
                    >
                      -
                    </button>
                    <span className="w-10 text-center font-bold text-primary">{tipo.quantidade}</span>
                    <button
                      type="button"
                      onClick={() => updateTipoQuantidade(i, tipo.quantidade + 1)}
                      className="w-8 h-8 bg-white border rounded-lg flex items-center justify-center hover:bg-gray-100"
                    >
                      +
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={() => navigate('/')} className="btn-outline">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={submitting || !clienteId || !mesReferencia}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Gerando...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Gerar Planejamento
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
