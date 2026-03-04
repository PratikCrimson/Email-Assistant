import React, { useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { RefreshCw, Mail, AlertCircle, Search, Inbox } from 'lucide-react'
import { fetchEmails } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import EmailDetailModal from '@/components/EmailDetailModal'

function getInitials(sender = '') {
    const match = sender.match(/^([^<@\s]+)/)
    const name = match ? match[1] : sender
    return name.slice(0, 2).toUpperCase()
}

const CATEGORY_ORDER = ['job', 'finance', 'hr', 'promotions', 'security', 'other']

function getCategoryLabel(category) {
    if (!category) return 'Other'
    return category.charAt(0).toUpperCase() + category.slice(1)
}

function EmailCard({ email, onClick }) {
    const date = email.date ? format(new Date(email.date), 'MMM d, h:mm a') : ''
    return (
        <button
            id={`email-card-${email.email_id}`}
            onClick={() => onClick(email)}
            className="group w-full text-left p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[hsl(var(--accent)/0.45)] hover:border-[hsl(var(--foreground)/0.22)] hover:shadow-[0_10px_24px_-18px_hsl(var(--foreground)/0.65)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]"
        >
            <div className="flex items-start gap-3">
                <div className="shrink-0 w-9 h-9 rounded-lg bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] flex items-center justify-center text-xs font-bold text-[hsl(var(--foreground)/0.75)]">
                    {getInitials(email.sender)}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="text-sm font-semibold text-[hsl(var(--foreground))] truncate group-hover:text-[hsl(var(--foreground))]">
                            {email.subject || '(No subject)'}
                        </p>
                        <span className="shrink-0 text-xs text-[hsl(var(--muted-foreground))]">{date}</span>
                    </div>
                    <p className="text-xs text-[hsl(var(--muted-foreground))] truncate mb-2">{email.sender}</p>
                    <div className="flex items-start justify-between gap-2">
                        <p className="text-xs text-[hsl(var(--muted-foreground))]/70 line-clamp-2 leading-relaxed">
                            {(email.body || email.preview || '').slice(0, 120)}
                        </p>
                        {email.category && (
                            <Badge
                                variant={email.category}
                                className="shrink-0 capitalize"
                            >
                                {email.category}
                            </Badge>
                        )}
                    </div>
                </div>
            </div>
        </button>
    )
}

// Module-level cache: survives navigation (component unmount/remount)
// Cleared only when the Refresh button is explicitly pressed.
let _emailCache = null

export default function EmailsPage() {
    const [emails, setEmails] = useState(_emailCache || [])
    const [loading, setLoading] = useState(_emailCache === null) // no spinner when cache exists
    const [error, setError] = useState(null)
    const [selected, setSelected] = useState(null)
    const [query, setQuery] = useState('')
    const [activeCategory, setActiveCategory] = useState('all')

    // forceRefresh=true is used by the Refresh button to bypass cache
    const load = async (forceRefresh = false) => {
        if (!forceRefresh && _emailCache !== null) return  // already have data
        setLoading(true)
        setError(null)
        try {
            const { data } = await fetchEmails()
            _emailCache = data.preview || []
            setEmails(_emailCache)
        } catch (err) {
            setError(err?.response?.data?.detail || 'Failed to load emails. Is the backend running?')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { load(false) }, [])

    const categoryCounts = useMemo(() => {
        const counts = {}
        for (const email of emails) {
            const key = (email.category || 'other').toLowerCase()
            counts[key] = (counts[key] || 0) + 1
        }
        return counts
    }, [emails])

    const categoryFilters = useMemo(() => {
        const ordered = CATEGORY_ORDER.filter((key) => categoryCounts[key] > 0)
        return ['all', ...ordered]
    }, [categoryCounts])

    useEffect(() => {
        if (activeCategory !== 'all' && !categoryFilters.includes(activeCategory)) {
            setActiveCategory('all')
        }
    }, [activeCategory, categoryFilters])

    const filteredEmails = useMemo(() => {
        const q = query.trim().toLowerCase()
        return emails.filter((email) => {
            const matchesCategory = activeCategory === 'all' || (email.category || 'other') === activeCategory
            if (!matchesCategory) return false
            if (!q) return true
            const haystack = `${email.subject || ''} ${email.sender || ''} ${email.body || ''} ${email.preview || ''}`.toLowerCase()
            return haystack.includes(q)
        })
    }, [emails, activeCategory, query])

    const latestEmailDate = useMemo(() => {
        const firstWithDate = emails.find((email) => email.date)
        if (!firstWithDate?.date) return null
        return format(new Date(firstWithDate.date), 'MMM d, yyyy h:mm a')
    }, [emails])

    return (
        <div className="p-4 sm:p-6 max-w-5xl mx-auto">
            <div className="mb-5 rounded-2xl border border-[hsl(var(--border))] bg-gradient-to-br from-[hsl(var(--card))] via-[hsl(var(--card))] to-[hsl(var(--secondary)/0.65)] overflow-hidden">
                <div className="p-5 sm:p-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                        <div className="flex items-center gap-2">
                            <div className="w-9 h-9 rounded-lg bg-[hsl(var(--foreground))] text-[hsl(var(--background))] flex items-center justify-center">
                                <Inbox className="h-4 w-4" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">Inbox</h1>
                                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">
                                    {emails.length > 0 ? `${emails.length} recent emails indexed` : 'Your latest emails'}
                                </p>
                            </div>
                        </div>
                    </div>
                    <Button id="refresh-emails-btn" variant="outline" size="sm" onClick={() => load(true)} disabled={loading}>
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>

                {!loading && !error && emails.length > 0 && (
                    <div className="px-5 sm:px-6 py-3 border-t border-[hsl(var(--border))] bg-[hsl(var(--background)/0.45)] flex flex-wrap items-center gap-2 text-xs">
                        <span className="inline-flex items-center rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-2.5 py-1 text-[hsl(var(--muted-foreground))]">
                            Latest email: {latestEmailDate || 'Unknown'}
                        </span>
                        {categoryFilters.filter((key) => key !== 'all').slice(0, 4).map((category) => (
                            <span
                                key={category}
                                className="inline-flex items-center rounded-md border border-[hsl(var(--border))] px-2.5 py-1 text-[hsl(var(--muted-foreground))]"
                            >
                                {getCategoryLabel(category)}: {categoryCounts[category]}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {!loading && !error && emails.length > 0 && (
                <div className="mb-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 sm:p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                        <div className="relative w-full lg:max-w-md">
                            <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]" />
                            <Input
                                id="inbox-filter-input"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Filter by subject, sender or preview..."
                                className="pl-9"
                            />
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {categoryFilters.map((category) => (
                                <button
                                    key={category}
                                    type="button"
                                    onClick={() => setActiveCategory(category)}
                                    className={cn(
                                        'rounded-md border px-2.5 py-1 text-xs font-medium transition-colors',
                                        activeCategory === category
                                            ? 'border-[hsl(var(--foreground)/0.25)] bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                                            : 'border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:border-[hsl(var(--foreground)/0.18)] hover:text-[hsl(var(--foreground))]'
                                    )}
                                >
                                    {category === 'all' ? 'All' : getCategoryLabel(category)}
                                    {category !== 'all' && ` (${categoryCounts[category] || 0})`}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {loading && (
                <div className="flex flex-col items-center justify-center py-24 gap-4">
                    <Spinner size="lg" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">Fetching your emails…</p>
                </div>
            )}

            {!loading && error && (
                <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
                    <AlertCircle className="h-10 w-10 text-[hsl(var(--destructive))]" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">{error}</p>
                    <Button id="retry-emails-btn" variant="outline" size="sm" onClick={load}>Retry</Button>
                </div>
            )}

            {!loading && !error && emails.length === 0 && (
                <div className="flex flex-col items-center justify-center py-24 gap-3">
                    <Mail className="h-10 w-10 text-[hsl(var(--muted-foreground))]" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">No emails found.</p>
                </div>
            )}

            {!loading && !error && emails.length > 0 && (
                <>
                    {filteredEmails.length === 0 ? (
                        <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 text-center">
                            <p className="text-sm text-[hsl(var(--muted-foreground))]">
                                No emails match your current filters.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-2.5">
                            {filteredEmails.map((email) => (
                                <EmailCard key={email.email_id} email={email} onClick={setSelected} />
                            ))}
                        </div>
                    )}
                </>
            )}

            <EmailDetailModal email={selected} onClose={() => setSelected(null)} />
        </div>
    )
}
