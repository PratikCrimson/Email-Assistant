import React, { useMemo, useState } from 'react'
import { format } from 'date-fns'
import { Badge } from '@/components/ui/badge'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { User, Calendar, Tag, Globe, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

function looksLikeHtml(value = '') {
    return /<[a-z][\s\S]*>/i.test(value)
}

function buildEmailSrcDoc(htmlBody = '') {
    return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root { color-scheme: light; }
      body {
        margin: 0;
        padding: 20px;
        font-family: Arial, Helvetica, sans-serif;
        color: #111827;
        line-height: 1.55;
        background: #ffffff;
      }
      img { max-width: 100%; height: auto; }
      table { max-width: 100%; border-collapse: collapse; }
      pre { white-space: pre-wrap; word-wrap: break-word; }
      blockquote { margin: 0; padding-left: 12px; border-left: 3px solid #d1d5db; color: #4b5563; }
      a { color: #2563eb; text-decoration: underline; }
    </style>
  </head>
  <body>${htmlBody}</body>
</html>`
}

export default function EmailDetailModal({ email, onClose }) {
    const dateStr = email?.date
        ? format(new Date(email.date), 'PPpp')
        : 'Unknown date'
    const htmlBody = email?.html_body || (looksLikeHtml(email?.body || '') ? (email?.body || '') : '')
    const hasHtml = Boolean(htmlBody)
    const plainTextBody = email?.body || email?.cleaned_body || email?.preview || 'No content available.'
    const [viewMode, setViewMode] = useState(hasHtml ? 'rendered' : 'text')

    const htmlDoc = useMemo(() => buildEmailSrcDoc(htmlBody), [htmlBody])
    if (!email) return null

    return (
        <Dialog open={!!email} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="w-[min(1100px,95vw)] max-w-none h-[90vh] p-0 overflow-hidden">
                <div className="flex h-full flex-col">
                    <div className="border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] px-5 py-4 md:px-6">
                        <DialogHeader>
                            <DialogTitle className="text-xl pr-10 leading-snug break-words">
                                {email.subject || '(No subject)'}
                            </DialogTitle>
                        </DialogHeader>

                        <div className="mt-3 grid gap-2 text-sm text-[hsl(var(--muted-foreground))] md:grid-cols-2">
                            <span className="flex items-center gap-1.5 min-w-0">
                                <User className="h-4 w-4 shrink-0" />
                                <span className="truncate">{email.sender || 'Unknown sender'}</span>
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Calendar className="h-4 w-4 shrink-0" />
                                {dateStr}
                            </span>
                            {email.category && (
                                <span className="flex items-center gap-1.5">
                                    <Tag className="h-4 w-4 shrink-0" />
                                    <Badge variant={email.category} className="capitalize">{email.category}</Badge>
                                </span>
                            )}
                        </div>

                        {hasHtml && (
                            <div className="mt-4 inline-flex rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--background))] p-1">
                                <button
                                    type="button"
                                    onClick={() => setViewMode('rendered')}
                                    className={cn(
                                        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                                        viewMode === 'rendered'
                                            ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                                            : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                                    )}
                                >
                                    <Globe className="h-3.5 w-3.5" />
                                    Rendered
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setViewMode('text')}
                                    className={cn(
                                        'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                                        viewMode === 'text'
                                            ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                                            : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                                    )}
                                >
                                    <FileText className="h-3.5 w-3.5" />
                                    Plain text
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 min-h-0 bg-[hsl(var(--background))]">
                        {hasHtml && viewMode === 'rendered' ? (
                            <iframe
                                title="Rendered email content"
                                sandbox=""
                                srcDoc={htmlDoc}
                                className="h-full w-full border-0 bg-white"
                                referrerPolicy="no-referrer"
                            />
                        ) : (
                            <div className="h-full overflow-auto px-5 py-5 md:px-6">
                                <pre className="whitespace-pre-wrap break-words text-sm text-[hsl(var(--foreground))]/90 leading-relaxed font-sans">
                                    {plainTextBody}
                                </pre>
                            </div>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}
