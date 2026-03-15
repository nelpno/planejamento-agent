import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api/client';
import type { Cliente } from '../types';

interface FormData {
  nome_empresa: string;
  nicho: string;
  publico_alvo: Record<string, any>;
  tom_de_voz: Record<string, any>;
  pilares: Array<{ nome: string; percentual: number; descricao: string }>;
  tipos_conteudo: Array<{ tipo: string; quantidade: number; formato?: string; duracao?: string; slides?: string }>;
  concorrentes: Array<{ nome: string; instagram?: string; site?: string }>;
  redes_sociais: Record<string, string>;
  instrucoes: string;
}

const emptyForm: FormData = {
  nome_empresa: '',
  nicho: '',
  publico_alvo: {},
  tom_de_voz: {},
  pilares: [{ nome: '', percentual: 0, descricao: '' }],
  tipos_conteudo: [{ tipo: 'video_roteiro', quantidade: 1 }],
  concorrentes: [{ nome: '' }],
  redes_sociais: {},
  instrucoes: '',
};

const tiposOptions = [
  { value: 'video_roteiro', label: 'Video / Roteiro' },
  { value: 'arte_estatica', label: 'Arte Estatica' },
  { value: 'carrossel', label: 'Carrossel' },
];

export default function ClienteForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [form, setForm] = useState<FormData>({ ...emptyForm });
  const [publicoAlvoText, setPublicoAlvoText] = useState('');
  const [tomDeVozText, setTomDeVozText] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEditing);

  useEffect(() => {
    if (id) {
      api.get<Cliente>(`/clientes/${id}`).then((res) => {
        const c = res.data;
        setForm({
          nome_empresa: c.nome_empresa,
          nicho: c.nicho,
          publico_alvo: c.publico_alvo || {},
          tom_de_voz: c.tom_de_voz || {},
          pilares: c.pilares?.length ? c.pilares : [{ nome: '', percentual: 0, descricao: '' }],
          tipos_conteudo: c.tipos_conteudo?.length ? c.tipos_conteudo : [{ tipo: 'video_roteiro', quantidade: 1 }],
          concorrentes: c.concorrentes?.length ? c.concorrentes : [{ nome: '' }],
          redes_sociais: c.redes_sociais || {},
          instrucoes: c.instrucoes || '',
        });
        setPublicoAlvoText(JSON.stringify(c.publico_alvo || {}, null, 2));
        setTomDeVozText(JSON.stringify(c.tom_de_voz || {}, null, 2));
        setLoading(false);
      }).catch(() => {
        navigate('/clientes');
      });
    }
  }, [id, navigate]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      let parsedPublico = form.publico_alvo;
      let parsedTom = form.tom_de_voz;
      try { parsedPublico = JSON.parse(publicoAlvoText || '{}'); } catch {}
      try { parsedTom = JSON.parse(tomDeVozText || '{}'); } catch {}

      const payload = {
        ...form,
        publico_alvo: parsedPublico,
        tom_de_voz: parsedTom,
        pilares: form.pilares.filter((p) => p.nome.trim()),
        tipos_conteudo: form.tipos_conteudo.filter((t) => t.tipo.trim()),
        concorrentes: form.concorrentes.filter((c) => c.nome.trim()),
      };

      if (isEditing) {
        await api.put(`/clientes/${id}`, payload);
      } else {
        await api.post('/clientes', payload);
      }
      navigate('/clientes');
    } catch (err) {
      console.error('Erro ao salvar cliente:', err);
      alert('Erro ao salvar cliente.');
    } finally {
      setSaving(false);
    }
  }

  function addPilar() { setForm({ ...form, pilares: [...form.pilares, { nome: '', percentual: 0, descricao: '' }] }); }
  function removePilar(i: number) { setForm({ ...form, pilares: form.pilares.filter((_, idx) => idx !== i) }); }
  function updatePilar(i: number, field: string, value: any) {
    const updated = [...form.pilares]; (updated[i] as any)[field] = value; setForm({ ...form, pilares: updated });
  }

  function addTipo() { setForm({ ...form, tipos_conteudo: [...form.tipos_conteudo, { tipo: 'video_roteiro', quantidade: 1 }] }); }
  function removeTipo(i: number) { setForm({ ...form, tipos_conteudo: form.tipos_conteudo.filter((_, idx) => idx !== i) }); }
  function updateTipo(i: number, field: string, value: any) {
    const updated = [...form.tipos_conteudo]; (updated[i] as any)[field] = value; setForm({ ...form, tipos_conteudo: updated });
  }

  function addConcorrente() { setForm({ ...form, concorrentes: [...form.concorrentes, { nome: '' }] }); }
  function removeConcorrente(i: number) { setForm({ ...form, concorrentes: form.concorrentes.filter((_, idx) => idx !== i) }); }
  function updateConcorrente(i: number, field: string, value: string) {
    const updated = [...form.concorrentes]; (updated[i] as any)[field] = value; setForm({ ...form, concorrentes: updated });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <button onClick={() => navigate('/clientes')} className="text-sm text-gray-500 hover:text-accent flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Voltar para Clientes
        </button>
        <h1 className="text-3xl font-bold text-primary mt-2">
          {isEditing ? 'Editar Cliente' : 'Novo Cliente'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Nome da Empresa *</label>
            <input className="input-field" value={form.nome_empresa} onChange={(e) => setForm({ ...form, nome_empresa: e.target.value })} required placeholder="Ex: Empresa XYZ" />
          </div>
          <div>
            <label className="label">Nicho *</label>
            <input className="input-field" value={form.nicho} onChange={(e) => setForm({ ...form, nicho: e.target.value })} required placeholder="Ex: Saude e Bem-estar" />
          </div>
        </div>

        <div>
          <label className="label">Publico-alvo (JSON)</label>
          <textarea className="input-field min-h-[80px] font-mono text-sm" value={publicoAlvoText} onChange={(e) => setPublicoAlvoText(e.target.value)} placeholder='{"idade": "25-45", "interesses": ["fitness"]}' />
        </div>

        <div>
          <label className="label">Tom de Voz (JSON)</label>
          <textarea className="input-field min-h-[80px] font-mono text-sm" value={tomDeVozText} onChange={(e) => setTomDeVozText(e.target.value)} placeholder='{"estilo": "profissional"}' />
        </div>

        {/* Pilares */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="label mb-0">Pilares de Conteudo</label>
            <button type="button" onClick={addPilar} className="text-sm text-accent hover:underline">+ Adicionar</button>
          </div>
          <div className="space-y-3">
            {form.pilares.map((pilar, i) => (
              <div key={i} className="flex gap-2 items-start">
                <input className="input-field flex-1" placeholder="Nome" value={pilar.nome} onChange={(e) => updatePilar(i, 'nome', e.target.value)} />
                <input className="input-field w-20" type="number" placeholder="%" value={pilar.percentual || ''} onChange={(e) => updatePilar(i, 'percentual', Number(e.target.value))} />
                <input className="input-field flex-1" placeholder="Descricao" value={pilar.descricao} onChange={(e) => updatePilar(i, 'descricao', e.target.value)} />
                {form.pilares.length > 1 && (
                  <button type="button" onClick={() => removePilar(i)} className="p-2 text-red-400 hover:text-red-600">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Tipos de conteudo */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="label mb-0">Tipos de Conteudo</label>
            <button type="button" onClick={addTipo} className="text-sm text-accent hover:underline">+ Adicionar</button>
          </div>
          <div className="space-y-3">
            {form.tipos_conteudo.map((tipo, i) => (
              <div key={i} className="flex gap-2 items-center">
                <select className="input-field flex-1" value={tipo.tipo} onChange={(e) => updateTipo(i, 'tipo', e.target.value)}>
                  {tiposOptions.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                </select>
                <input className="input-field w-24" type="number" min={1} placeholder="Qtd" value={tipo.quantidade} onChange={(e) => updateTipo(i, 'quantidade', Number(e.target.value))} />
                {form.tipos_conteudo.length > 1 && (
                  <button type="button" onClick={() => removeTipo(i)} className="p-2 text-red-400 hover:text-red-600">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Concorrentes */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="label mb-0">Concorrentes</label>
            <button type="button" onClick={addConcorrente} className="text-sm text-accent hover:underline">+ Adicionar</button>
          </div>
          <div className="space-y-3">
            {form.concorrentes.map((conc, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input className="input-field flex-1" placeholder="Nome" value={conc.nome} onChange={(e) => updateConcorrente(i, 'nome', e.target.value)} />
                <input className="input-field flex-1" placeholder="@instagram" value={conc.instagram || ''} onChange={(e) => updateConcorrente(i, 'instagram', e.target.value)} />
                <input className="input-field flex-1" placeholder="Site" value={conc.site || ''} onChange={(e) => updateConcorrente(i, 'site', e.target.value)} />
                {form.concorrentes.length > 1 && (
                  <button type="button" onClick={() => removeConcorrente(i)} className="p-2 text-red-400 hover:text-red-600">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Instrucoes Especiais</label>
          <textarea className="input-field min-h-[80px]" value={form.instrucoes} onChange={(e) => setForm({ ...form, instrucoes: e.target.value })} placeholder="Instrucoes adicionais..." />
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <button type="button" onClick={() => navigate('/clientes')} className="btn-outline">Cancelar</button>
          <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
            {saving ? 'Salvando...' : isEditing ? 'Atualizar' : 'Criar Cliente'}
          </button>
        </div>
      </form>
    </div>
  );
}
