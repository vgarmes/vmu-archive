'use client'

import { useEffect, useState } from 'react'

type Theme = 'auto' | 'light' | 'dark'
const THEMES: Theme[] = ['auto', 'light', 'dark']

const prefersDark = () => matchMedia('(prefers-color-scheme: dark)').matches

function apply(theme: Theme) {
	const dark = theme === 'dark' || (theme === 'auto' && prefersDark())
	document.documentElement.classList.toggle('dark', dark)
}

/** auto/light/dark switch; the initial class is set by a script in the layout. */
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
		<div className="flex gap-1 text-sm" role="group" aria-label="Theme">
			{THEMES.map(t => (
				<button
					key={t}
					type="button"
					aria-pressed={theme === t}
					onClick={() => choose(t)}
					className="text-muted-foreground hover:text-foreground border-primary hover:bg-primary hover:text-primary-foreground px-2 uppercase aria-pressed:border"
				>
					{t}
				</button>
			))}
		</div>
	)
}
