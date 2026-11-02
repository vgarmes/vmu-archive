'use client'

import { useEffect, useState } from 'react'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue
} from '@/components/ui/Select'

type Theme = 'auto' | 'light' | 'dark'
const THEMES = [
	{ value: 'auto', label: 'Auto' },
	{ value: 'light', label: 'Light' },
	{ value: 'dark', label: 'Dark' }
] as const satisfies { value: Theme; label: string }[]

const prefersDark = () => matchMedia('(prefers-color-scheme: dark)').matches

function apply(theme: Theme) {
	const dark = theme === 'dark' || (theme === 'auto' && prefersDark())
	document.documentElement.classList.toggle('dark', dark)
}

/** auto/light/dark menu; the initial class is set by a script in the layout. */
export default function ThemeToggle() {
	// Unknown until mounted: the server can't read localStorage.
	const [theme, setTheme] = useState<Theme | null>(null)

	useEffect(() => {
		let saved: Theme = 'auto'
		try {
			saved = (localStorage.getItem('theme') as Theme) ?? 'auto'
		} catch {}
		setTheme(saved)
		// Follow the system while in auto mode.
		const media = matchMedia('(prefers-color-scheme: dark)')
		const onChange = () => {
			try {
				if ((localStorage.getItem('theme') ?? 'auto') === 'auto') apply('auto')
			} catch {}
		}
		media.addEventListener('change', onChange)
		return () => media.removeEventListener('change', onChange)
	}, [])

	const choose = (next: Theme) => {
		try {
			localStorage.setItem('theme', next)
		} catch {}
		setTheme(next)
		apply(next)
	}

	return (
		<Select items={THEMES} value={theme} onValueChange={v => v && choose(v)}>
			{/* Blank until mounted, since the saved theme isn't known on the server. */}
			<SelectTrigger aria-label="Theme" size="xs" className="w-20 uppercase">
				<SelectValue>
					{(value: Theme | null) =>
						THEMES.find(t => t.value === value)?.label ?? null
					}
				</SelectValue>
			</SelectTrigger>
			<SelectContent
				alignItemWithTrigger={false}
				align="end"
				className="min-w-0! uppercase"
			>
				{THEMES.map(({ value, label }) => (
					<SelectItem key={value} value={value}>
						{label}
					</SelectItem>
				))}
			</SelectContent>
		</Select>
	)
}
