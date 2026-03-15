import type { Planejamento } from '../types';

type Status = Planejamento['status'];

const statusConfig: Record<Status, { label: string; classes: string }> = {
  rascunho: {
    label: 'Rascunho',
    classes: 'bg-gray-100 text-gray-700 border-gray-300',
  },
  em_geracao: {
    label: 'Em Geração',
    classes: 'bg-amber-50 text-amber-700 border-amber-300 animate-pulse',
  },
  revisao: {
    label: 'Revisão',
    classes: 'bg-blue-50 text-blue-700 border-blue-300',
  },
  aprovado: {
    label: 'Aprovado',
    classes: 'bg-green-50 text-green-700 border-green-300',
  },
  ajuste_solicitado: {
    label: 'Ajuste Solicitado',
    classes: 'bg-orange-50 text-orange-700 border-orange-300',
  },
  failed: {
    label: 'Falhou',
    classes: 'bg-red-50 text-red-700 border-red-300',
  },
};

interface StatusBadgeProps {
  status: Status;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status];
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${config.classes} ${sizeClasses}`}
    >
      {config.label}
    </span>
  );
}
