import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/lib/theme-provider'
import { Button } from '@/components/ui/button'

export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme()
    return (
        <Button
            id="theme-toggle-btn"
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
            {theme === 'dark'
                ? <Sun className="h-4 w-4" />
                : <Moon className="h-4 w-4" />
            }
            <span className="sr-only">Toggle theme</span>
        </Button>
    )
}
