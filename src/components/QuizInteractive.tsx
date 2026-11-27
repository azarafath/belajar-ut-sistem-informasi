import { useState, useEffect, useMemo } from 'preact/hooks';

export interface QuizOption {
  letter: string;
  text: string;
}

export interface PgQuestion {
  num: number;
  module: string;
  question: string;
  options: QuizOption[];
  answerLetter: string;
  explanation: string;
}

export interface EssayQuestion {
  num: number;
  question: string;
  answer: string;
}

interface Props {
  courseSlug: string;
  pgQuestions: PgQuestion[];
  essayQuestions?: EssayQuestion[];
}

export default function QuizInteractive({
  courseSlug,
  pgQuestions,
  essayQuestions = [],
}: Props) {
  const [mode, setMode] = useState<'practice' | 'read' | 'essay'>('practice');
  const [moduleFilter, setModuleFilter] = useState<string>('ALL');
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [shuffledOrder, setShuffledOrder] = useState<number[] | null>(null);
  const [revealedEssays, setRevealedEssays] = useState<Record<number, boolean>>({});

  const storageKey = `belajarut_quiz_${courseSlug}`;

  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed === 'object') setAnswers(parsed);
      }
    } catch {}
    const onSwitchMode = (e: Event) => {
      const detail = (e as CustomEvent<{ mode?: 'practice' | 'read' | 'essay' }>).detail;
      if (detail?.mode) setMode(detail.mode);
    };
    window.addEventListener('belajarut:quiz-mode', onSwitchMode);
    return () => window.removeEventListener('belajarut:quiz-mode', onSwitchMode);
  }, [storageKey]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(answers));
    } catch {}
  }, [answers, storageKey]);

  const modules = useMemo(() => {
    const set = new Set<string>();
    pgQuestions.forEach((q) => {
      if (q.module) set.add(q.module);
    });
    return Array.from(set).sort((a, b) => {
      const na = parseInt(a.replace(/\D/g, '') || '99', 10);
      const nb = parseInt(b.replace(/\D/g, '') || '99', 10);
      return na - nb;
    });
  }, [pgQuestions]);

  const filteredQuestions = useMemo(() => {
    const base =
      moduleFilter === 'ALL'
        ? pgQuestions
        : pgQuestions.filter((q) => q.module === moduleFilter);
    if (!shuffledOrder) return base;
    const byNum = new Map(base.map((q) => [q.num, q]));
    const ordered = shuffledOrder
      .map((n) => byNum.get(n))
      .filter((x): x is PgQuestion => Boolean(x));
    return ordered.length === base.length ? ordered : base;
  }, [pgQuestions, moduleFilter, shuffledOrder]);

  useEffect(() => {
    setCurrentIdx(0);
  }, [moduleFilter]);

  const stats = useMemo(() => {
    let correct = 0;
    let wrong = 0;
    pgQuestions.forEach((q) => {
      const chosen = answers[q.num];
      if (!chosen) return;
      if (chosen.toUpperCase() === q.answerLetter.toUpperCase()) correct++;
      else wrong++;
    });
    return { correct, wrong, total: pgQuestions.length };
  }, [pgQuestions, answers]);

  const currentQ = filteredQuestions[currentIdx];
  const chosenLetter = currentQ ? answers[currentQ.num] : undefined;
  const isCorrect =
    currentQ && chosenLetter
      ? chosenLetter.toUpperCase() === currentQ.answerLetter.toUpperCase()
      : false;

  const handleSelectOption = (letter: string) => {
    if (!currentQ || answers[currentQ.num]) return;
    setAnswers((prev) => ({ ...prev, [currentQ.num]: letter }));
  };

  const handleShuffle = () => {
    const baseNums = (
      moduleFilter === 'ALL'
        ? pgQuestions
        : pgQuestions.filter((q) => q.module === moduleFilter)
    ).map((q) => q.num);
    for (let i = baseNums.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [baseNums[i], baseNums[j]] = [baseNums[j], baseNums[i]];
    }
    setShuffledOrder(baseNums);
    setCurrentIdx(0);
  };

  const handleReset = () => {
    setAnswers({});
    setShuffledOrder(null);
    setCurrentIdx(0);
  };

  const progressPct =
    filteredQuestions.length > 0
      ? Math.round(((currentIdx + 1) / filteredQuestions.length) * 100)
      : 0;

  return (
    <section class="mod-card" id="quiz-pg">
      <div class="mod-head">
        <h2>Bank Soal &amp; Latihan Interaktif ({pgQuestions.length} PG{essayQuestions.length > 0 ? ` + ${essayQuestions.length} Essay` : ''})</h2>
        <span class="mod-tag">Ujian Tipe U</span>
      </div>

      <div class="quiz-mode-bar">
        <div class="quiz-tabs" role="tablist">
          <button
            type="button"
            class={`quiz-tab-btn ${mode === 'practice' ? 'is-active' : ''}`}
            onClick={() => setMode('practice')}
          >
            🎯 Mode Latihan
          </button>
          <button
            type="button"
            class={`quiz-tab-btn ${mode === 'read' ? 'is-active' : ''}`}
            onClick={() => setMode('read')}
          >
            📖 Mode Baca ({pgQuestions.length})
          </button>
          {essayQuestions.length > 0 && (
            <button
              type="button"
              class={`quiz-tab-btn ${mode === 'essay' ? 'is-active' : ''}`}
              onClick={() => setMode('essay')}
            >
              ✍️ Essay ({essayQuestions.length})
            </button>
          )}
        </div>

        <div class="quiz-stats">
          <span class="stat-pill is-ok">Benar: {stats.correct}</span>
          <span class="stat-pill is-err">Salah: {stats.wrong}</span>
          <span class="stat-pill">
            Sisa: {stats.total - stats.correct - stats.wrong}
          </span>
        </div>
      </div>

      {mode !== 'essay' && (
        <div class="quiz-filters">
          <button
            type="button"
            class={`filter-chip ${moduleFilter === 'ALL' ? 'is-active' : ''}`}
            onClick={() => {
              setModuleFilter('ALL');
              setShuffledOrder(null);
            }}
          >
            Semua ({pgQuestions.length})
          </button>
          {modules.map((m) => (
            <button
              key={m}
              type="button"
              class={`filter-chip ${moduleFilter === m ? 'is-active' : ''}`}
              onClick={() => {
                setModuleFilter(m);
                setShuffledOrder(null);
              }}
            >
              {m}
            </button>
          ))}
          {mode === 'practice' && (
            <>
              <button type="button" class="filter-chip" onClick={handleShuffle}>
                🔀 Acak
              </button>
              {(stats.correct > 0 || stats.wrong > 0) && (
                <button type="button" class="filter-chip" onClick={handleReset}>
                  ↺ Reset Skor
                </button>
              )}
            </>
          )}
        </div>
      )}

      {mode === 'practice' && currentQ && (
        <div>
          <div class="quiz-progress-track" aria-label="Progres Latihan">
            <div class="quiz-progress-fill" style={{ width: `${progressPct}%` }} />
          </div>

          <div class="quiz-stage-card" key={currentQ.num}>
            <div class="quiz-q-meta">
              <span>
                Soal {currentIdx + 1} dari {filteredQuestions.length} • {currentQ.module}
              </span>
              <span>#{currentQ.num}</span>
            </div>

            <p class="quiz-q-title">{currentQ.question}</p>

            <div class="quiz-opt-stack">
              {currentQ.options.map((opt, idx) => {
                const letter = opt.letter || String.fromCharCode(65 + idx);
                const isSelected = chosenLetter?.toUpperCase() === letter.toUpperCase();
                const isRightAns =
                  currentQ.answerLetter.toUpperCase() === letter.toUpperCase();

                let cls = 'quiz-opt-btn';
                if (chosenLetter) {
                  if (isRightAns) cls += ' is-correct';
                  else if (isSelected) cls += ' is-wrong';
                }

                return (
                  <button
                    key={letter}
                    type="button"
                    class={cls}
                    disabled={Boolean(chosenLetter)}
                    onClick={() => handleSelectOption(letter)}
                  >
                    <span class="quiz-opt-letter">{letter}</span>
                    <span>{opt.text}</span>
                  </button>
                );
              })}
            </div>

            {chosenLetter && (() => {
              const correctOpt = currentQ.options.find(
                (o, i) => (o.letter || String.fromCharCode(65 + i)).toUpperCase() === currentQ.answerLetter.toUpperCase()
              );
              const chosenOpt = currentQ.options.find(
                (o, i) => (o.letter || String.fromCharCode(65 + i)).toUpperCase() === chosenLetter.toUpperCase()
              );
              return (
                <div class={`quiz-feedback ${isCorrect ? 'is-ok' : 'is-err'}`}>
                  <strong>
                    {isCorrect
                      ? `✅ Benar! (${currentQ.answerLetter}. ${correctOpt?.text || ''})`
                      : `❌ Kurang tepat — Kamu memilih ${chosenLetter}${chosenOpt ? ` (${chosenOpt.text})` : ''}. Kunci: ${currentQ.answerLetter}${correctOpt ? `. ${correctOpt.text}` : ''}`}
                  </strong>
                  {currentQ.explanation && (
                    <p style={{ margin: '8px 0 0', lineHeight: 1.6 }}>
                      <strong>💡 Pembahasan:</strong> {currentQ.explanation}
                    </p>
                  )}
                </div>
              );
            })()}

            <div class="quiz-nav-row">
              <button
                type="button"
                class="quiz-nav-btn"
                disabled={currentIdx === 0}
                onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
              >
                ← Sebelumnya
              </button>
              <button
                type="button"
                class="quiz-nav-btn is-primary"
                disabled={currentIdx >= filteredQuestions.length - 1}
                onClick={() =>
                  setCurrentIdx((i) => Math.min(filteredQuestions.length - 1, i + 1))
                }
              >
                Soal Berikutnya →
              </button>
            </div>
          </div>
        </div>
      )}

      {mode === 'read' && (
        <div class="quiz-grid">
          {filteredQuestions.map((q) => (
            <div class="q-item" key={q.num}>
              <strong>{q.question}</strong>
              <ul class="opt-list">
                {q.options.map((opt, idx) => (
                  <li key={idx}>
                    {opt.letter ? `${opt.letter}. ${opt.text}` : opt.text}
                  </li>
                ))}
              </ul>
              <div>
                <span class="ans-pill">
                  Kunci: {q.answerLetter}
                  {q.explanation ? ` (${q.explanation})` : ''}
                </span>
              </div>
              <details class="explain-box">
                <summary>Lihat Pembahasan</summary>
                <ul class="explain-list">
                  {q.options.map((opt, idx) => {
                    const letter = opt.letter || String.fromCharCode(65 + idx);
                    const ok = letter.toUpperCase() === q.answerLetter.toUpperCase();
                    return (
                      <li key={idx} class={ok ? 'is-right' : 'is-wrong'}>
                        {letter}. {ok ? '(Benar) ' : '(Kurang tepat) '}
                        {ok && q.explanation ? q.explanation : opt.text}
                      </li>
                    );
                  })}
                </ul>
              </details>
            </div>
          ))}
        </div>
      )}

      {mode === 'essay' && essayQuestions.length > 0 && (
        <div class="quiz-grid">
          {essayQuestions.map((eq) => {
            const shown = Boolean(revealedEssays[eq.num]);
            return (
              <div class="q-item" key={eq.num}>
                <strong>{eq.question}</strong>
                <div style={{ marginTop: '8px' }}>
                  <button
                    type="button"
                    class="filter-chip"
                    onClick={() =>
                      setRevealedEssays((prev) => ({ ...prev, [eq.num]: !shown }))
                    }
                  >
                    {shown ? 'Sembunyikan Jawaban' : '👁️ Lihat Jawaban Essay'}
                  </button>
                </div>
                {shown && (
                  <div class="quiz-feedback is-ok" style={{ marginTop: '8px' }}>
                    {eq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

