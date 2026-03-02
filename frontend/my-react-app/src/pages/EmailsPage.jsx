import React, { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { RefreshCw, Mail, AlertCircle } from 'lucide-react'
import { fetchEmails } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import EmailDetailModal from '@/components/EmailDetailModal'

function getInitials(sender = '') {
    const match = sender.match(/^([^<@\s]+)/)
    const name = match ? match[1] : sender
    return name.slice(0, 2).toUpperCase()
}

function EmailCard({ email, onClick }) {
    const date = email.date ? format(new Date(email.date), 'MMM d') : ''
    return (
        <button
            id={`email-card-${email.email_id}`}
            onClick={() => onClick(email)}
            className="w-full text-left p-4 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--card))]/60 hover:bg-[hsl(var(--card))] hover:border-white/20 transition-all duration-150 group"
        >
            <div className="flex items-start gap-3">
                {/* Avatar */}
                <div className="shrink-0 w-9 h-9 rounded bg-white/8 border border-white/10 flex items-center justify-center text-xs font-bold text-white/70">
                    {getInitials(email.sender)}
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-0.5">
                        <p className="text-sm font-semibold text-[hsl(var(--foreground))] truncate">
                            {email.subject || '(No subject)'}
                        </p>
                        <span className="shrink-0 text-xs text-[hsl(var(--muted-foreground))]">{date}</span>
                    </div>
                    <p className="text-xs text-[hsl(var(--muted-foreground))] truncate mb-2">{email.sender}</p>
                    <div className="flex items-center justify-between gap-2">
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

    return (
        <div className="p-6 max-w-3xl mx-auto">
            {/* Page header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">Inbox</h1>
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">
                        {emails.length > 0 ? `${emails.length} recent emails` : 'Your latest emails'}
                    </p>
                </div>
                <Button id="refresh-emails-btn" variant="outline" size="sm" onClick={() => load(true)} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </Button>
            </div>

            {/* States */}
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
                <div className="space-y-2.5">
                    {emails.map((email) => (
                        <EmailCard key={email.email_id} email={email} onClick={setSelected} />
                    ))}
                </div>
            )}

            <EmailDetailModal email={selected} onClose={() => setSelected(null)} />
        </div>
    )
}
