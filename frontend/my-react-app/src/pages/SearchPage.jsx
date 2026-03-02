import React, { useState } from 'react'
import { format } from 'date-fns'
import { Search, AlertCircle, Inbox } from 'lucide-react'
import { semanticSearch } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import EmailDetailModal from '@/components/EmailDetailModal'

function ResultCard({ result, onClick }) {
    const date = result.date ? format(new Date(result.date), 'MMM d, yyyy') : ''
    const pct = result.distance != null ? Math.round((1 - Math.min(result.distance, 1)) * 100) : null

    return (
        <button
            id={`search-result-${result.email_id}`}
            onClick={() => onClick(result)}
            className="w-full text-left p-4 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--card))] hover:bg-[hsl(var(--accent))] transition-colors duration-150"
        >
            <div className="flex items-start justify-between gap-3 mb-1">
                <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                    {result.subject || '(No subject)'}
                </p>
                <div className="flex items-center gap-2 shrink-0">
                    {pct !== null && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
                            {pct}% match
                        </span>
                    )}
                    {result.category && <Badge variant={result.category} className="capitalize">{result.category}</Badge>}
                </div>
            </div>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mb-1.5">
                {result.sender} · {date}
            </p>
            <p className="text-xs text-[hsl(var(--muted-foreground))]/70 leading-relaxed line-clamp-2">
                {result.preview}
            </p>
        </button>
    )
}

export default function SearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [selected, setSelected] = useState(null)

    const handleSearch = async (e) => {
        e?.preventDefault()
        if (!query.trim()) return
        setLoading(true)
        setError(null)
        try {
            const { data } = await semanticSearch({ q: query, limit: 10 })
            setResults(data.results || [])
        } catch (err) {
            setError(err?.response?.data?.detail || 'Search failed. Is the backend running?')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="p-6 max-w-3xl mx-auto">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">Search</h1>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">
                    Find emails by meaning, not just keywords.
                </p>
            </div>

            <form onSubmit={handleSearch} className="flex gap-2 mb-6">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                    <Input
                        id="search-query-input"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. interview schedule next week…"
                        className="pl-9"
                    />
                </div>
                <Button id="search-submit-btn" type="submit" disabled={loading || !query.trim()}>
                    {loading ? <Spinner size="sm" /> : <Search className="h-4 w-4" />}
                    Search
                </Button>
            </form>

            {loading && (
                <div className="flex flex-col items-center justify-center py-24 gap-4">
                    <Spinner size="lg" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">Searching…</p>
                </div>
            )}

            {!loading && error && (
                <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
                    <AlertCircle className="h-10 w-10 text-[hsl(var(--destructive))]" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">{error}</p>
                </div>
            )}

            {!loading && results !== null && results.length === 0 && !error && (
                <div className="flex flex-col items-center justify-center py-24 gap-3">
                    <Inbox className="h-10 w-10 text-[hsl(var(--muted-foreground))]" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">No results for "{query}"</p>
                </div>
            )}

            {!loading && results && results.length > 0 && (
                <div className="space-y-2">
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mb-3">
                        {results.length} result{results.length !== 1 ? 's' : ''} for <span className="text-[hsl(var(--foreground))] font-medium">"{query}"</span>
                    </p>
                    {results.map((r) => (
                        <ResultCard key={r.email_id} result={r} onClick={setSelected} />
                    ))}
                </div>
            )}

            <EmailDetailModal email={selected} onClose={() => setSelected(null)} />
        </div>
    )
}
