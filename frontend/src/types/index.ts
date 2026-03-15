export interface Cliente {
  id: string;
  nome_empresa: string;
  nicho: string;
  publico_alvo: Record<string, any>;
  tom_de_voz: Record<string, any>;
  pilares: Array<{ nome: string; percentual: number; descricao: string }>;
  tipos_conteudo: Array<{ tipo: string; quantidade: number; formato?: string; duracao?: string; slides?: string }>;
  concorrentes: Array<{ nome: string; instagram?: string; site?: string }>;
  redes_sociais: Record<string, string>;
  instrucoes: string | null;
  logo_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Planejamento {
  id: string;
  cliente_id: string;
  mes_referencia: string;
  status: 'rascunho' | 'em_geracao' | 'revisao' | 'aprovado' | 'ajuste_solicitado' | 'failed';
  resumo_estrategico: string | null;
  temas: Array<{ tema: string; pilar: string; justificativa: string }> | null;
  calendario: Array<{ data: string; tipo_conteudo?: string; tipo?: string; titulo: string }> | null;
  inputs_extras: string | null;
  pesquisa: Record<string, any> | null;
  feedback: string | null;
  pdf_url: string | null;
  pipeline_logs: Record<string, any> | null;
  pipeline_duration: number | null;
  foco: string | null;
  destino_conversao: string | null;
  tipo_conteudo_uso: string | null;
  plataformas: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface Conteudo {
  id: string;
  planejamento_id: string;
  tipo: 'video_roteiro' | 'arte_estatica' | 'carrossel';
  pilar: string | null;
  framework: string | null;
  titulo: string;
  conteudo: Record<string, any>;
  variacoes_ab: Array<{ copy_alternativa: string }> | null;
  referencia_visual: string | null;
  ordem: number;
  created_at: string;
}

export interface PipelineLog {
  agent_name: string;
  iteration: number;
  decision: string;
  reasoning: string | null;
  duration_ms: number | null;
  created_at: string | null;
}
