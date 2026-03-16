import { useState } from 'react';
import type { PipelineLog } from '../types';

const PIPELINE_STEPS = [
  { key: 'pesquisador', label: 'Pesquisador', icon: SearchIcon },
  { key: 'gerador', label: 'Gerador', icon: PlanIcon },
];

function SearchIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );
}

function PlanIcon() {
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  );
}

type StepStatus = 'waiting' | 'running' | 'done' | 'error';

interface PipelineProgressProps {
  logs: PipelineLog[];
  currentAgent?: string;
}

export default function PipelineProgress({ logs, currentAgent }: PipelineProgressProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  function getStepStatus(stepKey: string): StepStatus {
    const stepLogs = logs.filter(
      (l) => l.agent_name.toLowerCase().includes(stepKey)
    );
    if (stepLogs.length === 0) {
      if (currentAgent?.toLowerCase().includes(stepKey)) return 'running';
      return 'waiting';
    }
    const lastLog = stepLogs[stepLogs.length - 1];
    if (lastLog.decision.includes('error') || lastLog.decision.includes('failed')) return 'error';
    if (lastLog.decision.includes('completed') || lastLog.decision === 'done' || lastLog.decision === 'finish') return 'done';
    if (currentAgent?.toLowerCase().includes(stepKey)) return 'running';
    return 'done';
  }

  function getStepLogs(stepKey: string): PipelineLog[] {
    return logs.filter((l) => l.agent_name.toLowerCase().includes(stepKey));
  }

  const statusStyles: Record<StepStatus, string> = {
    waiting: 'border-gray-300 bg-gray-50 text-gray-400',
    running: 'border-accent bg-accent/10 text-accent animate-pulse',
    done: 'border-green-500 bg-green-50 text-green-600',
    error: 'border-red-500 bg-red-50 text-red-600',
  };

  const statusLabels: Record<StepStatus, string> = {
    waiting: 'Aguardando',
    running: 'Executando...',
    done: 'Concluído',
    error: 'Erro',
  };

  return (
    <div className="card">
      <h3 className="text-lg font-bold text-primary mb-6">
        Pipeline de Geração
      </h3>

      <div className="space-y-4">
        {PIPELINE_STEPS.map((step, index) => {
          const status = getStepStatus(step.key);
          const stepLogs = getStepLogs(step.key);
          const isExpanded = expandedStep === step.key;

          return (
            <div key={step.key}>
              {/* Connector line */}
              {index > 0 && (
                <div className="flex justify-center -mt-4 -mb-4 py-0">
                  <div className={`w-0.5 h-4 ${status === 'waiting' ? 'bg-gray-200' : 'bg-green-300'}`} />
                </div>
              )}

              {/* Step */}
              <button
                onClick={() => setExpandedStep(isExpanded ? null : step.key)}
                className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${statusStyles[status]}`}
              >
                <div className="flex-shrink-0">
                  <step.icon />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold">{step.label}</p>
                  <p className="text-xs opacity-75">{statusLabels[status]}</p>
                </div>
                {stepLogs.length > 0 && (
                  <svg
                    className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </button>

              {/* Expanded logs */}
              {isExpanded && stepLogs.length > 0 && (
                <div className="mt-2 ml-9 space-y-2">
                  {stepLogs.map((log, i) => (
                    <div key={i} className="bg-gray-50 rounded-lg p-3 text-sm border border-gray-100">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-700">
                          Iteração {log.iteration} - {log.decision}
                        </span>
                        {log.duration_ms && (
                          <span className="text-xs text-gray-500">
                            {(log.duration_ms / 1000).toFixed(1)}s
                          </span>
                        )}
                      </div>
                      {log.reasoning && (
                        <p className="text-gray-600 text-xs mt-1">{log.reasoning}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
