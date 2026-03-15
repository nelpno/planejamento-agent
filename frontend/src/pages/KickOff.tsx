import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import type { Cliente } from '../types';

const CANAIS_OPTIONS = ['Meta', 'Google', 'TikTok', 'YouTube', 'LinkedIn'];

const STEP_TITLES = [
  'Sobre a Empresa',
  'Objetivos & Vendas',
  'Mercado & Concorrência',
  'Produto & Diferencial',
  'Público-Alvo',
];

const STEP_ICONS = [
  // Building
  <svg key="1" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>,
  // Target
  <svg key="2" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  // Globe
  <svg key="3" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>,
  // Star
  <svg key="4" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>,
  // Users
  <svg key="5" className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>,
];

interface KickOffForm {
  nome_empresa: string;
  nicho: string;
  instagram: string;
  site: string;
  sobre_empresa: string;
  momento: string;
  envolvidos: string;
  objetivos_curto: string;
  objetivos_longo: string;
  objetivo_trafego: string;
  justificativas: string;
  media_vendas: string;
  ticket_medio: string;
  lucro_liquido: string;
  crm: string;
  canais: string[];
  estrategias_vencedoras: string;
  canal_mais_vende: string;
  investimento_midia: string;
  sazonalidade: string;
  concorrentes: string;
  preco_relativo: string;
  marcas_referencia: string;
  produtos_mais_vendidos: string;
  puv: string;
  forcas: string;
  fraquezas: string;
  oportunidades: string;
  ameacas: string;
  publico1: string;
  publico2: string;
  publico3: string;
}

const initialForm: KickOffForm = {
  nome_empresa: '',
  nicho: '',
  instagram: '',
  site: '',
  sobre_empresa: '',
  momento: '',
  envolvidos: '',
  objetivos_curto: '',
  objetivos_longo: '',
  objetivo_trafego: '',
  justificativas: '',
  media_vendas: '',
  ticket_medio: '',
  lucro_liquido: '',
  crm: '',
  canais: [],
  estrategias_vencedoras: '',
  canal_mais_vende: '',
  investimento_midia: '',
  sazonalidade: '',
  concorrentes: '',
  preco_relativo: '',
  marcas_referencia: '',
  produtos_mais_vendidos: '',
  puv: '',
  forcas: '',
  fraquezas: '',
  oportunidades: '',
  ameacas: '',
  publico1: '',
  publico2: '',
  publico3: '',
};

function buildKickoffText(form: KickOffForm): string {
  const lines = [
    `Instagram: ${form.instagram || 'Não informado'}`,
    `Site: ${form.site || 'Não informado'}`,
    `Sobre a empresa: ${form.sobre_empresa || 'Não informado'}`,
    `Momento atual da empresa: ${form.momento || 'Não informado'}`,
    `Principais envolvidos no projeto: ${form.envolvidos || 'Não informado'}`,
    `Objetivos a curto prazo (6 meses): ${form.objetivos_curto || 'Não informado'}`,
    `Objetivos a longo prazo (1-2 anos): ${form.objetivos_longo || 'Não informado'}`,
    `Principal objetivo com tráfego: ${form.objetivo_trafego || 'Não informado'}`,
    `Justificativas para o projeto: ${form.justificativas || 'Não informado'}`,
    `Média de vendas por mês: ${form.media_vendas || 'Não informado'}`,
    `Ticket médio últimos 3 meses: ${form.ticket_medio || 'Não informado'}`,
    `Lucro líquido por mês: ${form.lucro_liquido || 'Não informado'}`,
    `CRM utilizado: ${form.crm || 'Não informado'}`,
    `Canais já utilizados: ${form.canais.length > 0 ? form.canais.join(', ') : 'Não informado'}`,
    `Histórico de estratégias vencedoras e processo de vendas: ${form.estrategias_vencedoras || 'Não informado'}`,
    `Canal que mais vende: ${form.canal_mais_vende || 'Não informado'}`,
    `Valor investido em mídia e resultados: ${form.investimento_midia || 'Não informado'}`,
    `Peculiaridades sazonais: ${form.sazonalidade || 'Não informado'}`,
    `Principais concorrentes: ${form.concorrentes || 'Não informado'}`,
    `Preço em relação aos concorrentes: ${form.preco_relativo || 'Não informado'}`,
    `Marcas de referência: ${form.marcas_referencia || 'Não informado'}`,
    `Produtos/serviços mais vendidos: ${form.produtos_mais_vendidos || 'Não informado'}`,
    `PUV (Proposta Única de Valor): ${form.puv || 'Não informado'}`,
    `Forças (SWOT): ${form.forcas || 'Não informado'}`,
    `Fraquezas (SWOT): ${form.fraquezas || 'Não informado'}`,
    `Oportunidades (SWOT): ${form.oportunidades || 'Não informado'}`,
    `Ameaças (SWOT): ${form.ameacas || 'Não informado'}`,
    `Público-alvo 1: ${form.publico1 || 'Não informado'}`,
    `Público-alvo 2: ${form.publico2 || 'Não informado'}`,
    `Público-alvo 3: ${form.publico3 || 'Não informado'}`,
  ];
  return lines.join('\n');
}

export default function KickOff() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [form, setForm] = useState<KickOffForm>(initialForm);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Cliente | null>(null);
  const [error, setError] = useState('');

  function updateField(field: keyof KickOffForm, value: string | string[]) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function toggleCanal(canal: string) {
    setForm((prev) => ({
      ...prev,
      canais: prev.canais.includes(canal)
        ? prev.canais.filter((c) => c !== canal)
        : [...prev.canais, canal],
    }));
  }

  function canAdvance(): boolean {
    if (currentStep === 1) {
      return form.nome_empresa.trim() !== '' && form.nicho.trim() !== '';
    }
    return true;
  }

  async function handleGenerate() {
    setLoading(true);
    setError('');
    try {
      const kickoff_text = buildKickoffText(form);
      const res = await api.post<Cliente>('/clientes/kick-off', {
        nome_empresa: form.nome_empresa,
        nicho: form.nicho,
        kickoff_text,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Erro ao gerar perfil com IA. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }

  function handleRegenerate() {
    setResult(null);
    setError('');
    handleGenerate();
  }

  // Input component helpers
  function TextInput({ label, field, placeholder, prefix }: { label: string; field: keyof KickOffForm; placeholder?: string; prefix?: string }) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
        <div className={prefix ? 'flex' : ''}>
          {prefix && (
            <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
              {prefix}
            </span>
          )}
          <input
            type="text"
            value={form[field] as string}
            onChange={(e) => updateField(field, e.target.value)}
            placeholder={placeholder}
            className={`w-full px-4 py-2.5 border border-gray-300 ${prefix ? 'rounded-r-lg' : 'rounded-lg'} focus:ring-2 focus:ring-accent/30 focus:border-accent outline-none transition-all text-sm`}
          />
        </div>
      </div>
    );
  }

  function TextArea({ label, field, placeholder, rows = 3, tooltip }: { label: string; field: keyof KickOffForm; placeholder?: string; rows?: number; tooltip?: string }) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          {label}
          {tooltip && (
            <span className="ml-1.5 inline-block relative group">
              <svg className="w-4 h-4 inline text-gray-400 cursor-help" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                {tooltip}
              </span>
            </span>
          )}
        </label>
        <textarea
          value={form[field] as string}
          onChange={(e) => updateField(field, e.target.value)}
          placeholder={placeholder}
          rows={rows}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent/30 focus:border-accent outline-none transition-all text-sm resize-none"
        />
      </div>
    );
  }

  function SelectInput({ label, field, options }: { label: string; field: keyof KickOffForm; options: { value: string; label: string }[] }) {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
        <select
          value={form[field] as string}
          onChange={(e) => updateField(field, e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent/30 focus:border-accent outline-none transition-all text-sm bg-white"
        >
          <option value="">Selecione...</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    );
  }

  // Render steps
  function renderStep() {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <TextInput label="Nome da Empresa *" field="nome_empresa" placeholder="Ex: Clínica Bella Vida" />
              <TextInput label="Nicho *" field="nicho" placeholder="Ex: Estética e Beleza" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <TextInput label="Instagram" field="instagram" placeholder="clinicabellavida" prefix="@" />
              <TextInput label="Site" field="site" placeholder="www.clinicabellavida.com.br" prefix="https://" />
            </div>
            <TextArea label="Conte um pouco sobre a empresa" field="sobre_empresa" placeholder="História, o que faz, diferenciais, tempo de mercado..." rows={4} />
            <SelectInput
              label="Momento atual da empresa"
              field="momento"
              options={[
                { value: 'Estagnada', label: 'Estagnada' },
                { value: 'Crescimento leve', label: 'Crescimento leve' },
                { value: 'Crescimento acelerado', label: 'Crescimento acelerado' },
                { value: 'Em queda', label: 'Em queda' },
              ]}
            />
            <TextArea label="Principais envolvidos no projeto (nome e cargo)" field="envolvidos" placeholder="Ex: João Silva - CEO, Maria Santos - Marketing" rows={2} />
          </div>
        );
      case 2:
        return (
          <div className="space-y-5">
            <TextArea label="Objetivos a curto prazo (6 meses)" field="objetivos_curto" placeholder="Ex: Aumentar faturamento em 30%, dobrar a captação de leads..." />
            <TextArea label="Objetivos a longo prazo (1-2 anos)" field="objetivos_longo" placeholder="Ex: Abrir segunda unidade, tornar-se referência no nicho..." />
            <TextArea label="Principal objetivo com tráfego" field="objetivo_trafego" placeholder="Ex: Gerar leads qualificados, aumentar vendas online..." />
            <TextArea label="Justificativas para o projeto" field="justificativas" placeholder="Por que investir em marketing digital agora?" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <TextInput label="Média de vendas por mês" field="media_vendas" placeholder="Ex: 50 vendas" />
              <TextInput label="Ticket médio (3 meses)" field="ticket_medio" placeholder="Ex: R$ 2.500" />
              <TextInput label="Lucro líquido mensal" field="lucro_liquido" placeholder="Ex: R$ 30.000" />
            </div>
            <TextInput label="CRM utilizado" field="crm" placeholder="Ex: RD Station, HubSpot, Pipedrive..." />
          </div>
        );
      case 3:
        return (
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Canais já utilizados</label>
              <div className="flex flex-wrap gap-2">
                {CANAIS_OPTIONS.map((canal) => (
                  <button
                    key={canal}
                    type="button"
                    onClick={() => toggleCanal(canal)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 border ${
                      form.canais.includes(canal)
                        ? 'bg-accent text-white border-accent shadow-md shadow-accent/20'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-accent hover:text-accent'
                    }`}
                  >
                    {canal}
                  </button>
                ))}
              </div>
            </div>
            <TextArea label="Histórico de estratégias vencedoras + Processo de vendas" field="estrategias_vencedoras" placeholder="O que já funcionou? Como é o processo de vendas atualmente?" rows={4} />
            <TextInput label="Canal que mais vende" field="canal_mais_vende" placeholder="Ex: Instagram, Indicação, Google..." />
            <TextArea label="Valor investido em mídia e resultados" field="investimento_midia" placeholder="Ex: R$ 5.000/mês em Meta Ads, gerando 200 leads..." />
            <TextArea label="Peculiaridades sazonais" field="sazonalidade" placeholder="Ex: Vendas aumentam em datas comemorativas, inverno é baixa temporada..." />
            <TextArea label="Principais concorrentes" field="concorrentes" placeholder="Ex: @concorrente1 - Clínica XYZ (www.xyz.com.br)" rows={3} />
            <SelectInput
              label="Preço em relação aos concorrentes"
              field="preco_relativo"
              options={[
                { value: 'Mais barato', label: 'Mais barato' },
                { value: 'Na média', label: 'Na média' },
                { value: 'Mais caro', label: 'Mais caro' },
              ]}
            />
            <TextArea label="Marcas de referência" field="marcas_referencia" placeholder="Marcas que admira, mesmo que de outro segmento..." rows={2} />
          </div>
        );
      case 4:
        return (
          <div className="space-y-5">
            <TextArea label="Produtos/serviços mais vendidos" field="produtos_mais_vendidos" placeholder="Liste os principais produtos ou serviços..." rows={3} />
            <TextArea
              label="PUV - Proposta Única de Valor"
              field="puv"
              placeholder="O que torna sua empresa única? Por que o cliente deve escolher você?"
              rows={3}
              tooltip="O que diferencia sua empresa de todos os concorrentes. O motivo pelo qual o cliente escolhe VOCÊ."
            />
            <div className="border border-gray-200 rounded-xl p-5 bg-gray-50/50">
              <h3 className="text-sm font-semibold text-primary mb-4 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                Análise SWOT
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <TextArea label="Forças" field="forcas" placeholder="Pontos fortes da empresa..." rows={3} />
                <TextArea label="Fraquezas" field="fraquezas" placeholder="Pontos a melhorar..." rows={3} />
                <TextArea label="Oportunidades" field="oportunidades" placeholder="Oportunidades de mercado..." rows={3} />
                <TextArea label="Ameaças" field="ameacas" placeholder="Ameaças externas..." rows={3} />
              </div>
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-5">
            <TextArea
              label="Público-alvo 1 (principal)"
              field="publico1"
              placeholder="Ex: Mulher 30-50 anos, classe A/B, executiva, que busca procedimentos estéticos de alta qualidade, mora em capitais..."
              rows={4}
            />
            <TextArea
              label="Público-alvo 2 (opcional)"
              field="publico2"
              placeholder="Descreva um segundo perfil de público, se houver..."
              rows={3}
            />
            <TextArea
              label="Público-alvo 3 (opcional)"
              field="publico3"
              placeholder="Descreva um terceiro perfil de público, se houver..."
              rows={3}
            />
          </div>
        );
      default:
        return null;
    }
  }

  // Preview result
  if (result) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-primary">Perfil Gerado com IA</h1>
          <p className="text-gray-500 mt-1">Revise o perfil do cliente antes de salvar</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Publico-alvo */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
              Publico-Alvo
            </h3>
            <p className="text-sm text-gray-600 mb-2">{result.publico_alvo?.descricao}</p>
            <div className="flex flex-wrap gap-2 mb-2">
              {result.publico_alvo?.faixa_etaria && (
                <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full">{result.publico_alvo.faixa_etaria} anos</span>
              )}
              {result.publico_alvo?.localizacao && (
                <span className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded-full">{result.publico_alvo.localizacao}</span>
              )}
            </div>
            {result.publico_alvo?.dores?.length > 0 && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 mb-1">Dores:</p>
                <ul className="space-y-1">
                  {result.publico_alvo.dores.map((d: string, i: number) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-1.5">
                      <span className="text-accent mt-0.5">&#x2022;</span> {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Tom de Voz */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
              Tom de Voz
            </h3>
            <p className="text-sm text-gray-600 mb-3"><strong>Estilo:</strong> {result.tom_de_voz?.estilo}</p>
            {result.tom_de_voz?.palavras_chave?.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium text-gray-500 mb-1">Palavras-chave:</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.tom_de_voz.palavras_chave.map((p: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full">{p}</span>
                  ))}
                </div>
              </div>
            )}
            {result.tom_de_voz?.evitar?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Evitar:</p>
                <div className="flex flex-wrap gap-1.5">
                  {result.tom_de_voz.evitar.map((e: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 bg-red-50 text-red-600 text-xs rounded-full">{e}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Pilares */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
              Pilares de Conteudo
            </h3>
            <div className="space-y-3">
              {result.pilares?.map((p, i) => (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{p.nome}</span>
                    <span className="text-sm font-bold text-accent">{p.percentual}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div className="bg-accent h-2 rounded-full transition-all" style={{ width: `${p.percentual}%` }} />
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{p.descricao}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Tipos de Conteudo */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
              <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              Tipos de Conteudo
            </h3>
            <div className="space-y-2">
              {result.tipos_conteudo?.map((t, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-700">{t.tipo.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-gray-500">{t.formato} {t.duracao ? `| ${t.duracao}` : ''} {t.slides ? `| ${t.slides} slides` : ''}</p>
                  </div>
                  <span className="text-lg font-bold text-secondary">x{t.quantidade}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Concorrentes */}
          {result.concorrentes?.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg>
                Concorrentes
              </h3>
              <div className="space-y-2">
                {result.concorrentes.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
                    <div className="w-8 h-8 bg-secondary/10 rounded-full flex items-center justify-center text-secondary text-xs font-bold">
                      {i + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700">{c.nome}</p>
                      <p className="text-xs text-gray-500">{c.instagram} {c.site ? `| ${c.site}` : ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Instrucoes */}
          {result.instrucoes && (
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
              <h3 className="font-bold text-primary mb-3 flex items-center gap-2">
                <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                Instrucoes Especiais
              </h3>
              <p className="text-sm text-gray-600 whitespace-pre-line">{result.instrucoes}</p>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-center gap-4 pb-8">
          <button
            onClick={handleRegenerate}
            disabled={loading}
            className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-medium hover:border-accent hover:text-accent transition-all disabled:opacity-50"
          >
            {loading ? 'Gerando...' : 'Gerar Novamente'}
          </button>
          <button
            onClick={() => navigate('/clientes')}
            className="px-8 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-all shadow-lg shadow-green-600/20"
          >
            Salvar Cliente
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="max-w-2xl mx-auto flex flex-col items-center justify-center h-[60vh]">
        <div className="relative mb-6">
          <div className="w-20 h-20 border-4 border-accent/20 rounded-full" />
          <div className="absolute inset-0 w-20 h-20 border-4 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
        <h2 className="text-xl font-bold text-primary mb-2">Analisando respostas com IA...</h2>
        <p className="text-gray-500 text-center max-w-md">
          Estamos processando as respostas do kick-off para gerar o perfil completo do cliente.
          Isso pode levar alguns segundos.
        </p>
      </div>
    );
  }

  // Form
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-primary">Kick Off Inteligente</h1>
        <p className="text-gray-500 mt-1">Responda as perguntas e a IA criara o perfil do cliente automaticamente</p>
      </div>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-3">
          {STEP_TITLES.map((title, i) => {
            const step = i + 1;
            const isActive = step === currentStep;
            const isCompleted = step < currentStep;
            return (
              <button
                key={step}
                onClick={() => {
                  if (step < currentStep || canAdvance()) setCurrentStep(step);
                }}
                className={`flex items-center gap-2 text-sm font-medium transition-all ${
                  isActive ? 'text-accent' : isCompleted ? 'text-green-600' : 'text-gray-400'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                  isActive
                    ? 'bg-accent text-white shadow-md shadow-accent/30'
                    : isCompleted
                      ? 'bg-green-100 text-green-600'
                      : 'bg-gray-100 text-gray-400'
                }`}>
                  {isCompleted ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : step}
                </div>
                <span className="hidden md:inline">{title}</span>
              </button>
            );
          })}
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="bg-accent h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${(currentStep / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 md:p-8 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center text-accent">
            {STEP_ICONS[currentStep - 1]}
          </div>
          <div>
            <h2 className="text-lg font-bold text-primary">{STEP_TITLES[currentStep - 1]}</h2>
            <p className="text-xs text-gray-400">Etapa {currentStep} de 5</p>
          </div>
        </div>

        {renderStep()}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
          disabled={currentStep === 1}
          className="px-6 py-2.5 border border-gray-300 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Anterior
        </button>

        {currentStep < 5 ? (
          <button
            onClick={() => {
              if (canAdvance()) setCurrentStep((s) => Math.min(5, s + 1));
            }}
            disabled={!canAdvance()}
            className="px-6 py-2.5 bg-accent text-white rounded-xl font-medium hover:bg-accent/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-md shadow-accent/20"
          >
            Proximo
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ) : (
          <button
            onClick={handleGenerate}
            disabled={!canAdvance()}
            className="px-8 py-3 bg-accent text-white rounded-xl font-bold hover:bg-accent/90 transition-all disabled:opacity-50 shadow-lg shadow-accent/30 flex items-center gap-2 text-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Gerar Perfil com IA
          </button>
        )}
      </div>
    </div>
  );
}
