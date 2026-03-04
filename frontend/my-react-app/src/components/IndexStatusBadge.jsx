import React, { useEffect, useState, useRef } from 'react'
import { Activity, CheckCircle2 } from 'lucide-react'
import { getIndexStatus } from '@/lib/api'

function parseAsUtc(isoString) {
    if (!isoString) return null
    const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(isoString)
    return new Date(hasTimezone ? isoString : `${isoString}Z`)
}

export default function IndexStatusBadge() {
    const [status, setStatus] = useState(null)
    const intervalRef = useRef(null)

    const poll = async () => {
        try {
            const { data } = await getIndexStatus()
            setStatus(data)
        } catch {
            // Ignore transient polling errors; the next poll will retry.
            return
        }
    }

    useEffect(() => {
        const initialPollTimer = setTimeout(poll, 0)
        intervalRef.current = setInterval(poll, 4000)
        return () => {
            clearTimeout(initialPollTimer)
            clearInterval(intervalRef.current)
        }
    }, [])

    if (!status) return null

    const { running, processed, total, last_synced_at } = status

    if (running) {
        const pct = total > 0 ? Math.round((processed / total) * 100) : 0
        return (
            <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md border border-blue-500/30 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10">
                <Activity className="h-3 w-3 animate-pulse" />
                <span>Indexing {processed}/{total} ({pct}%)</span>
            </div>
        )
    }

    const parsedSyncedAt = last_synced_at ? parseAsUtc(last_synced_at) : null
    const syncedDate = parsedSyncedAt && !Number.isNaN(parsedSyncedAt.getTime())
        ? parsedSyncedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : null

    return (
        <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] bg-[hsl(var(--secondary))]">
            <CheckCircle2 className="h-3 w-3 text-emerald-500" />
            <span>{syncedDate ? `Synced ${syncedDate}` : 'Ready'}</span>
        </div>
    )
}
