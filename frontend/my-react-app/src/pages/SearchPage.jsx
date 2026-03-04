import React, { useState } from 'react'
import { format } from 'date-fns'
import { Search, AlertCircle, Inbox, SlidersHorizontal } from 'lucide-react'
import { semanticSearch } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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

const CATEGORY_OPTIONS = [
    { value: 'all', label: 'All categories' },
    { value: 'job', label: 'Job' },
    { value: 'finance', label: 'Finance' },
    { value: 'hr', label: 'HR' },
    { value: 'promotions', label: 'Promotions' },
    { value: 'security', label: 'Security' },
    { value: 'other', label: 'Other' },
]

function categoryLabel(value) {
    const found = CATEGORY_OPTIONS.find((opt) => opt.value === value)
    return found ? found.label : value
}

export default function SearchPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [selected, setSelected] = useState(null)
    const [showFilters, setShowFilters] = useState(false)
    const [filterCategory, setFilterCategory] = useState('all')
    const [filterSender, setFilterSender] = useState('')
    const [filterStartDate, setFilterStartDate] = useState('')
    const [filterEndDate, setFilterEndDate] = useState('')
    const [filterError, setFilterError] = useState('')

    const activeFilters = []
    if (filterCategory !== 'all') activeFilters.push(`Category: ${categoryLabel(filterCategory)}`)
    if (filterSender.trim()) activeFilters.push(`Sender: ${filterSender.trim()}`)
    if (filterStartDate) activeFilters.push(`From: ${filterStartDate}`)
    if (filterEndDate) activeFilters.push(`To: ${filterEndDate}`)

    const handleSearch = async (e) => {
        e?.preventDefault()
        if (!query.trim()) return
        if (filterStartDate && filterEndDate && filterStartDate > filterEndDate) {
            setFilterError('Start date cannot be after end date.')
            return
        }
        setFilterError('')

        const params = { q: query, limit: 10 }
        if (filterCategory !== 'all') params.category = filterCategory
        if (filterSender.trim()) params.from_sender = filterSender.trim()
        if (filterStartDate) params.start_date = `${filterStartDate}T00:00:00`
        if (filterEndDate) params.end_date = `${filterEndDate}T23:59:59`

        setLoading(true)
        setError(null)
        try {
            const { data } = await semanticSearch(params)
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

            <div className="mb-6">
                <div className="flex items-center gap-2 mb-2">
                    <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setShowFilters((v) => !v)}
                    >
                        <SlidersHorizontal className="h-3.5 w-3.5" />
                        Filters
                    </Button>
                    {(filterCategory !== 'all' || filterSender || filterStartDate || filterEndDate) && (
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                                setFilterCategory('all')
                                setFilterSender('')
                                setFilterStartDate('')
                                setFilterEndDate('')
                                setFilterError('')
                            }}
                        >
                            Clear
                        </Button>
                    )}
                </div>

                {showFilters && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                        <Select value={filterCategory} onValueChange={setFilterCategory}>
                            <SelectTrigger id="search-filter-category">
                                <SelectValue placeholder="Category" />
                            </SelectTrigger>
                            <SelectContent>
                                {CATEGORY_OPTIONS.map((opt) => (
                                    <SelectItem key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        <Input
                            id="search-filter-sender"
                            value={filterSender}
                            onChange={(e) => setFilterSender(e.target.value)}
                            placeholder="Sender (email/name)"
                        />

                        <Input
                            id="search-filter-start-date"
                            type="date"
                            value={filterStartDate}
                            onChange={(e) => setFilterStartDate(e.target.value)}
                        />

                        <Input
                            id="search-filter-end-date"
                            type="date"
                            value={filterEndDate}
                            onChange={(e) => setFilterEndDate(e.target.value)}
                        />
                    </div>
                )}

                {filterError && (
                    <p className="mt-2 text-xs text-[hsl(var(--destructive))]">{filterError}</p>
                )}

                {activeFilters.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                        {activeFilters.map((chip) => (
                            <span
                                key={chip}
                                className="inline-flex items-center rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--secondary))] px-2 py-1 text-[11px] text-[hsl(var(--muted-foreground))]"
                            >
                                {chip}
                            </span>
                        ))}
                    </div>
                )}
            </div>

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
