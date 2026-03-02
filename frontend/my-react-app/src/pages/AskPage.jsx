import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { askRag } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'

const SUGGESTIONS = [
    'Summarise my HR emails from this month',
    'Any interview invitations received recently?',
    'What bank transactions were mentioned?',
    'Any promotional offers expiring soon?',
]

function Message({ role, content }) {
    const isUser = role === 'user'
    return (
        <div className={cn('flex gap-3 animate-message', isUser ? 'flex-row-reverse' : 'flex-row')}>
            <div
                className={cn(
                    'shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
                    isUser
                        ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                        : 'bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--foreground))]'
                )}
            >
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>
            <div
                className={cn(
                    'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                    isUser
                        ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))] rounded-tr-sm'
                        : 'bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--foreground))] rounded-tl-sm'
                )}
            >
                {content}
            </div>
        </div>
    )
}

function TypingBubble() {
    return (
        <div className="flex gap-3 animate-message">
            <div className="shrink-0 w-8 h-8 rounded-full bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] flex items-center justify-center">
                <Bot className="h-4 w-4 text-[hsl(var(--foreground))]" />
            </div>
            <div className="bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--muted-foreground))] animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--muted-foreground))] animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-[hsl(var(--muted-foreground))] animate-bounce [animation-delay:300ms]" />
            </div>
        </div>
    )
}

export default function AskPage() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const bottomRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading])

    const send = async (text) => {
        const q = (text || input).trim()
        if (!q || loading) return
        setInput('')
        setMessages((m) => [...m, { role: 'user', content: q }])
        setLoading(true)
        try {
            const { data } = await askRag({ query: q })
            setMessages((m) => [...m, { role: 'assistant', content: data.answer }])
        } catch (err) {
            setMessages((m) => [
                ...m,
                { role: 'assistant', content: `Error: ${err?.response?.data?.detail || 'Something went wrong.'}` },
            ])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="px-6 py-4 border-b border-[hsl(var(--border))] shrink-0">
                <h1 className="text-xl font-bold flex items-center gap-2 text-[hsl(var(--foreground))]">
                    Ask AI
                    <Sparkles className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                </h1>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mt-0.5">
                    Ask questions about your emails in plain language.
                </p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
                        <div className="w-12 h-12 rounded-xl bg-[hsl(var(--foreground))] flex items-center justify-center">
                            <Sparkles className="h-6 w-6 text-[hsl(var(--background))]" />
                        </div>
                        <div>
                            <h2 className="text-base font-semibold mb-1 text-[hsl(var(--foreground))]">How can I help?</h2>
                            <p className="text-sm text-[hsl(var(--muted-foreground))] max-w-sm">
                                Ask me anything about your emails. I'll search through them and give you a clear answer.
                            </p>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                            {SUGGESTIONS.map((s) => (
                                <button
                                    key={s}
                                    onClick={() => send(s)}
                                    className="text-left text-sm px-4 py-3 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--card))] hover:bg-[hsl(var(--accent))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--accent-foreground))] transition-colors duration-150"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((m, i) => (
                    <Message key={i} role={m.role} content={m.content} />
                ))}
                {loading && <TypingBubble />}
                <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div className="px-6 py-4 border-t border-[hsl(var(--border))] shrink-0">
                <form
                    onSubmit={(e) => { e.preventDefault(); send() }}
                    className="flex gap-2"
                >
                    <Input
                        id="ask-query-input"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask about your emails…"
                        className="flex-1"
                        disabled={loading}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
                        }}
                    />
                    <Button
                        id="ask-send-btn"
                        type="submit"
                        disabled={loading || !input.trim()}
                        size="icon"
                    >
                        {loading ? <Spinner size="sm" /> : <Send className="h-4 w-4" />}
                    </Button>
                </form>
            </div>
        </div>
    )
}
