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

const PICK = 'themepick'

/** The saved theme (null until mounted) and a setter that saves and applies it. */
function useTheme() {
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
		// The header mounts two of these (row and mobile menu); keep them agreeing.
		const onPick = (e: Event) => setTheme((e as CustomEvent<Theme>).detail)
		window.addEventListener(PICK, onPick)
		return () => {
			media.removeEventListener('change', onChange)
			window.removeEventListener(PICK, onPick)
		}
	}, [])

	const choose = (next: Theme) => {
		try {
			localStorage.setItem('theme', next)
		} catch {}
		apply(next)
		window.dispatchEvent(new CustomEvent(PICK, { detail: next }))
	}

	return [theme, choose] as const
}

/** auto/light/dark menu; the initial class is set by a script in the layout. */
export default function ThemeToggle() {
	const [theme, choose] = useTheme()

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

/** The same choice as a row of buttons, for the mobile menu. */
export function ThemeButtons() {
	const [theme, choose] = useTheme()

	return (
		<div role="radiogroup" aria-label="Theme" className="flex gap-1">
			{THEMES.map(({ value, label }) => (
				<button
					key={value}
					type="button"
					role="radio"
					aria-checked={theme === value}
					onClick={() => choose(value)}
					className="text-muted-foreground hover:text-foreground focus-visible:ring-ring/50 aria-checked:bg-foreground aria-checked:text-background flex h-6 items-center px-2 text-xs tracking-[0.2em] uppercase outline-none focus-visible:ring-3"
				>
					{label}
				</button>
			))}
		</div>
	)
}
