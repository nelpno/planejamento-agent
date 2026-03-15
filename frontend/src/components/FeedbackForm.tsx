import { useState } from 'react';

interface FeedbackFormProps {
  onSubmit: (feedback: string) => void;
  loading?: boolean;
}

export default function FeedbackForm({ onSubmit, loading }: FeedbackFormProps) {
  const [feedback, setFeedback] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (feedback.trim()) {
      onSubmit(feedback.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card border-orange-200 bg-orange-50/30">
      <h4 className="font-bold text-primary mb-3 flex items-center gap-2">
        <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
        Solicitar Ajuste
      </h4>
      <textarea
        className="input-field min-h-[120px] resize-y"
        placeholder="Descreva os ajustes necessários no planejamento..."
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        required
      />
      <div className="mt-3 flex justify-end">
        <button
          type="submit"
          disabled={loading || !feedback.trim()}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
          Enviar Ajuste
        </button>
      </div>
    </form>
  );
}
