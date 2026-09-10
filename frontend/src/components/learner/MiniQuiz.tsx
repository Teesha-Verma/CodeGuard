import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, RotateCcw, ArrowRight } from 'lucide-react';

interface MiniQuizProps {
  quiz: {
    question: string;
    options: string[];
    correctIndex: number;
    explanation: string;
  };
  onComplete?: (passed: boolean) => void;
}

export const MiniQuiz: React.FC<MiniQuizProps> = ({ quiz, onComplete }) => {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = () => {
    if (selectedIndex === null) return;
    setIsSubmitted(true);
    const passed = selectedIndex === quiz.correctIndex;
    onComplete?.(passed);
  };

  const handleReset = () => {
    setSelectedIndex(null);
    setIsSubmitted(false);
  };

  const letters = ['A', 'B', 'C', 'D'];

  return (
    <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0d111a] p-5 sm:p-6 shadow-xs">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400">
          <HelpCircle className="w-4 h-4" />
        </div>
        <span className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
          Knowledge Check · 1 Question
        </span>
      </div>

      <h4 className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100 mb-4 leading-snug">
        {quiz.question}
      </h4>

      {/* Options */}
      <div className="space-y-2.5">
        {quiz.options.map((option, idx) => {
          const isSelected = selectedIndex === idx;
          const isCorrect = idx === quiz.correctIndex;
          let style =
            'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40 text-slate-800 dark:text-slate-200';

          if (isSubmitted) {
            if (isCorrect) {
              style =
                'border-emerald-500/60 bg-emerald-500/10 text-emerald-800 dark:text-emerald-300 font-medium';
            } else if (isSelected && !isCorrect) {
              style = 'border-rose-500/60 bg-rose-500/10 text-rose-800 dark:text-rose-300';
            } else {
              style = 'opacity-50 border-slate-200 dark:border-slate-800';
            }
          } else if (isSelected) {
            style =
              'border-blue-500 bg-blue-50/60 dark:bg-blue-950/40 text-blue-900 dark:text-blue-200 ring-1 ring-blue-500 font-medium';
          }

          return (
            <button
              key={idx}
              type="button"
              disabled={isSubmitted}
              onClick={() => setSelectedIndex(idx)}
              className={`w-full text-left p-3 rounded-md border text-xs flex items-start gap-3 transition-colors cursor-pointer disabled:cursor-default ${style}`}
            >
              <span
                className={`w-5 h-5 rounded flex items-center justify-center font-mono font-bold text-[11px] shrink-0 ${
                  isSubmitted && isCorrect
                    ? 'bg-emerald-600 text-white'
                    : isSubmitted && isSelected && !isCorrect
                    ? 'bg-rose-600 text-white'
                    : isSelected
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
              >
                {letters[idx]}
              </span>
              <span className="flex-1 leading-relaxed font-mono text-[11.5px] break-all">{option}</span>
              {isSubmitted && isCorrect && (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              )}
              {isSubmitted && isSelected && !isCorrect && (
                <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
              )}
            </button>
          );
        })}
      </div>

      {/* Explanation Banner */}
      {isSubmitted && (
        <div
          className={`mt-4 p-3 rounded-md text-xs leading-relaxed border ${
            selectedIndex === quiz.correctIndex
              ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-500/30 text-emerald-900 dark:text-emerald-300'
              : 'bg-rose-50 dark:bg-rose-950/30 border-rose-500/30 text-rose-900 dark:text-rose-300'
          }`}
        >
          <span className="font-bold block mb-1">
            {selectedIndex === quiz.correctIndex ? '✓ Correct Answer' : '✕ Incorrect Answer'}
          </span>
          <p className="text-[11px] font-sans">{quiz.explanation}</p>
        </div>
      )}

      {/* Action Footer */}
      <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
        {!isSubmitted ? (
          <button
            type="button"
            disabled={selectedIndex === null}
            onClick={handleSubmit}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-colors disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
          >
            <span>Check Answer</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span>Retake Quiz</span>
          </button>
        )}
      </div>
    </div>
  );
};
