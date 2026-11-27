import { useState, useEffect, useRef, useMemo } from 'preact/hooks';

interface SearchEntry {
  type: string;
  semester: number;
  course: string;
  title: string;
  snippet: string;
  url: string;
  keywords: string;
}

export default function SearchModal() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [entries, setEntries] = useState<SearchEntry[] | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      } else if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    const onClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      if (target?.closest('[data-open-search]')) {
        e.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener('keydown', onKey);
    document.addEventListener('click', onClick);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.removeEventListener('click', onClick);
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    setTimeout(() => inputRef.current?.focus(), 30);
    if (!entries) {
      fetch('/search-index.json')
        .then((r) => r.json())
        .then((data) => setEntries(data))
        .catch(() => setEntries([]));
    }
  }, [open, entries]);

  const results = useMemo(() => {
    if (!entries) return [];
    const q = query.trim().toLowerCase();
    if (!q) return entries.filter((e) => e.type === 'Matkul').slice(0, 14);
    const terms = q.split(/\s+/);
    return entries
      .filter((item) => terms.every((t) => item.keywords.includes(t)))
      .slice(0, 24);
  }, [entries, query]);

  if (!open) return null;

  return (
    <div
      class="astro-search-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div class="astro-search-dialog" role="dialog" aria-modal="true" aria-label="Cari Materi & Soal">
        <div class="astro-search-head">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            class="astro-search-input"
            placeholder="Cari matkul, modul, ahli, atau soal (mis. normalisasi, Hofstede, Big-O)..."
            value={query}
            onInput={(e) => setQuery((e.target as HTMLInputElement).value)}
          />
          <button
            type="button"
            class="astro-search-close"
            aria-label="Tutup pencarian"
            onClick={() => setOpen(false)}
          >
            ✕
          </button>
        </div>

        <div class="astro-search-results">
          {!entries ? (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--muted)' }}>
              Memuat indeks pencarian...
            </div>
          ) : results.length === 0 ? (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--muted)' }}>
              Tidak ada hasil untuk "{query}".
            </div>
          ) : (
            results.map((r, i) => (
              <a
                key={`${r.url}-${i}`}
                href={r.url}
                class="astro-search-item"
                onClick={() => setOpen(false)}
              >
                <div class="astro-search-meta">
                  <span>Smt {r.semester}</span>
                  <span>•</span>
                  <span>{r.type}</span>
                  <span>•</span>
                  <span>{r.course}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: '14px' }}>{r.title}</div>
                <div style={{ fontSize: '12.5px', color: 'var(--muted)', marginTop: '2px' }}>
                  {r.snippet}
                </div>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

