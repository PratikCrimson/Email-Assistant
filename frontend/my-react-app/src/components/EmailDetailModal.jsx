import React from 'react'
import { format } from 'date-fns'
import { Badge } from '@/components/ui/badge'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Mail, User, Calendar, Tag } from 'lucide-react'

export default function EmailDetailModal({ email, onClose }) {
    if (!email) return null

    const dateStr = email.date
        ? format(new Date(email.date), 'PPpp')
        : 'Unknown date'

    return (
        <Dialog open={!!email} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle className="text-xl pr-8 leading-snug">{email.subject || '(No subject)'}</DialogTitle>
                </DialogHeader>

                <div className="flex flex-wrap gap-4 text-sm text-[hsl(var(--muted-foreground))] mt-1">
                    <span className="flex items-center gap-1.5">
                        <User className="h-4 w-4" />
                        {email.sender}
                    </span>
                    <span className="flex items-center gap-1.5">
                        <Calendar className="h-4 w-4" />
                        {dateStr}
                    </span>
                    {email.category && (
                        <span className="flex items-center gap-1.5">
                            <Tag className="h-4 w-4" />
                            <Badge variant={email.category}>{email.category}</Badge>
                        </span>
                    )}
                </div>

                <div className="mt-4 border-t border-[hsl(var(--border))] pt-4">
                    <pre className="whitespace-pre-wrap text-sm text-[hsl(var(--foreground))]/90 leading-relaxed font-sans">
                        {email.body || email.preview || email.cleaned_body || 'No content available.'}
                    </pre>
                </div>
            </DialogContent>
        </Dialog>
    )
}
