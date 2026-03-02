import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export function Spinner({ className, size = 'default' }) {
    const sizes = { sm: 'h-4 w-4', default: 'h-6 w-6', lg: 'h-8 w-8' }
    return (
        <Loader2
            className={cn('animate-spin text-[hsl(var(--primary))]', sizes[size] || sizes.default, className)}
        />
    )
}
