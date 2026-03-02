import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Mail, Search, MessageSquare, LogIn, ChevronRight } from 'lucide-react'
import IndexStatusBadge from '@/components/IndexStatusBadge'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { cn } from '@/lib/utils'

const navItems = [
    {
        to: '/dashboard/emails',
        icon: Mail,
        label: 'Inbox',
        description: 'View your latest emails',
    },
    {
        to: '/dashboard/search',
        icon: Search,
        label: 'Search',
        description: 'Semantic email search',
    },
    {
        to: '/dashboard/ask',
        icon: MessageSquare,
        label: 'Ask AI',
        description: 'Ask questions about emails',
    },
]

function SidebarNavItem({ to, icon: Icon, label, description }) {
    return (
        <NavLink
            to={to}
            id={`nav-${label.toLowerCase().replace(' ', '-')}`}
            className={({ isActive }) =>
                cn(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-150',
                    isActive
                        ? 'bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))] font-medium'
                        : 'text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--accent-foreground))]'
                )
            }
        >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1 leading-tight">{label}</span>
            <ChevronRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-40 transition-opacity" />
        </NavLink>
    )
}

export default function DashboardLayout() {
    return (
        <div className="flex h-screen overflow-hidden bg-[hsl(var(--background))]">
            {/* ── Sidebar ─────────────────────────────────────────── */}
            <aside className="flex w-60 shrink-0 flex-col border-r border-[hsl(var(--sidebar-border))] bg-[hsl(var(--sidebar-bg))]">

                {/* Brand */}
                <div className="flex items-center gap-3 px-4 py-5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--foreground))]">
                        <Mail className="h-4 w-4 text-[hsl(var(--background))]" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-semibold leading-none text-[hsl(var(--foreground))]">
                            Email Assistant
                        </p>
                        <p className="mt-0.5 text-[11px] text-[hsl(var(--muted-foreground))]">
                            AI-powered inbox
                        </p>
                    </div>
                </div>

                <div className="mx-4 h-px bg-[hsl(var(--sidebar-border))]" />

                {/* Nav section */}
                <div className="flex-1 overflow-y-auto px-2 py-3">
                    <p className="mb-1.5 px-3 text-[11px] font-medium tracking-wider text-[hsl(var(--muted-foreground))] uppercase">
                        Navigation
                    </p>
                    <nav className="space-y-0.5">
                        {navItems.map((item) => (
                            <SidebarNavItem key={item.to} {...item} />
                        ))}
                    </nav>
                </div>

                {/* Sidebar footer */}
                <div className="border-t border-[hsl(var(--sidebar-border))] px-2 py-3">
                    <a
                        href="/auth/login"
                        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--accent-foreground))] transition-colors"
                    >
                        <LogIn className="h-3.5 w-3.5" />
                        Switch Google account
                    </a>
                </div>
            </aside>

            {/* ── Main area ────────────────────────────────────────── */}
            <div className="flex flex-1 flex-col overflow-hidden">

                {/* Top bar */}
                <header className="flex h-14 shrink-0 items-center justify-between border-b border-[hsl(var(--border))] bg-[hsl(var(--background))] px-6">
                    {/* Page breadcrumb — populated by each page via context if needed; placeholder for now */}
                    <div className="flex items-center gap-2 text-sm text-[hsl(var(--muted-foreground))]">
                        <Mail className="h-4 w-4" />
                        <span className="text-[hsl(var(--foreground))] font-medium">Email Assistant</span>
                    </div>

                    {/* Right side controls */}
                    <div className="flex items-center gap-2">
                        <IndexStatusBadge />
                        <div className="h-5 w-px bg-[hsl(var(--border))]" />
                        <ThemeToggle />
                    </div>
                </header>

                {/* Page scroll area */}
                <main className="flex-1 overflow-y-auto">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
