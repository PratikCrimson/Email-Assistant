import React from 'react'
import { Mail, ArrowRight, Search, MessageSquare, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'

const features = [
    { icon: Search, label: 'Semantic Search', desc: 'Find emails by meaning' },
    { icon: MessageSquare, label: 'Ask AI', desc: 'Get instant answers' },
    { icon: Zap, label: 'Auto-Sync', desc: 'Always up to date' },
]

export default function LoginPage() {
    return (
        <div className="min-h-screen flex bg-[hsl(var(--background))]">
            {/* Left panel */}
            <div className="hidden lg:flex w-1/2 flex-col justify-between bg-[hsl(var(--foreground))] p-10 text-[hsl(var(--background))]">
                <div className="flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(var(--background))]">
                        <Mail className="h-4 w-4 text-[hsl(var(--foreground))]" />
                    </div>
                    <span className="text-sm font-semibold">Email Assistant</span>
                </div>

                <div>
                    <blockquote className="text-2xl font-semibold leading-snug tracking-tight mb-4">
                        "Your emails, finally under control. Ask anything, find anything, instantly."
                    </blockquote>
                    <div className="flex flex-col gap-3 mt-8">
                        {features.map(({ icon: Icon, label, desc }) => (
                            <div key={label} className="flex items-center gap-3 opacity-80">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[hsl(var(--background))]/15">
                                    <Icon className="h-4 w-4" />
                                </div>
                                <div>
                                    <p className="text-sm font-medium leading-tight">{label}</p>
                                    <p className="text-xs opacity-70">{desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <p className="text-xs opacity-50">Email Assistant — AI Inbox</p>
            </div>

            {/* Right panel — sign in form */}
            <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
                {/* Mobile logo */}
                <div className="mb-8 flex items-center gap-2.5 lg:hidden">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--foreground))]">
                        <Mail className="h-4 w-4 text-[hsl(var(--background))]" />
                    </div>
                    <span className="text-base font-semibold">Email Assistant</span>
                </div>

                <div className="w-full max-w-sm">
                    <div className="mb-8">
                        <h1 className="text-2xl font-bold tracking-tight text-[hsl(var(--foreground))]">
                            Welcome back
                        </h1>
                        <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                            Sign in with your Google account to access your AI-powered inbox.
                        </p>
                    </div>

                    <Button
                        id="google-signin-btn"
                        onClick={() => { window.location.href = '/auth/login' }}
                        variant="outline"
                        size="lg"
                        className="w-full justify-start gap-3"
                    >
                        <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        Continue with Google
                        <ArrowRight className="ml-auto h-4 w-4 opacity-50" />
                    </Button>

                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-[hsl(var(--border))]" />
                        </div>
                        <div className="relative flex justify-center text-xs">
                            <span className="bg-[hsl(var(--background))] px-2 text-[hsl(var(--muted-foreground))]">
                                Secured by Google OAuth 2.0
                            </span>
                        </div>
                    </div>

                    <p className="text-center text-[11px] text-[hsl(var(--muted-foreground))]">
                        Read-only Gmail access. Your data stays on your device and is never shared.
                    </p>
                </div>
            </div>
        </div>
    )
}
