'use client'

import { cn } from 'cn'
import { type ReactNode, useEffect, useId, useRef, useState } from 'react'

export interface GameTab {
	/** Its value in the URL, ?tab=<id>; the first tab has none. */
	id: string
	label: string
	/** How many things it holds, shown after the label. */
	count?: number
	panel: ReactNode
}

/**
 * A game page's sections as tabs (Screens, Sprites, Fonts, Notes), so any one
 * is a click or a key away instead of below the others. The first tab is the
 * default; another is kept in the URL as ?tab=<id>, alongside whatever else
 * is there (?screen=, ?q=). Every panel stays mounted, hidden when not
 * selected, so a panel's state (the screens' search, scroll) survives a
 * switch.
 *
 * Keys: the number keys 1-9 pick a tab (not while typing, with a modifier, or
 * with a dialog open); in the tab bar, the arrow keys, Home and End move
 * between tabs, as a tablist does.
 */
export default function GameTabs({
	tabs,
	label
}: {
	tabs: GameTab[]
	label: string
}) {
	const [selected, setSelected] = useState(tabs[0].id)
	const [restored, setRestored] = useState(false)
	const refs = useRef<(HTMLButtonElement | null)[]>([])
	const base = useId()

	// The tab in the URL. A link to one screen always shows the screens, so
	// its ?tab= is dropped there and then: whatever writes the URL next (the
	// screens' drawer, as it opens or closes) mustn't carry it on.
	useEffect(() => {
		const params = new URLSearchParams(location.search)
		const fromUrl = params.get('tab')
		if (params.get('screen')) {
			if (fromUrl) {
				params.delete('tab')
				history.replaceState(history.state, '', `?${params}`)
			}
		} else if (tabs.some(t => t.id === fromUrl)) setSelected(fromUrl!)
		setRestored(true)
	}, [tabs])

	useEffect(() => {
		if (!restored) return
		const params = new URLSearchParams(location.search)
		if (selected === tabs[0].id) params.delete('tab')
		else params.set('tab', selected)
		const qs = params.toString()
		history.replaceState(history.state, '', qs ? `?${qs}` : location.pathname)
	}, [selected, restored, tabs])

	// Number keys pick a tab.
	useEffect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (
				e.defaultPrevented ||
				e.metaKey ||
				e.ctrlKey ||
				e.altKey ||
				e.shiftKey
			)
				return
			const n = Number(e.key)
			if (!Number.isInteger(n) || n < 1 || n > tabs.length) return
			const target = e.target as HTMLElement | null
			if (
				target?.closest('input, textarea, select, [contenteditable="true"]') ||
				document.querySelector('[role="dialog"]')
			)
				return
			e.preventDefault()
			setSelected(tabs[n - 1].id)
		}
		addEventListener('keydown', onKey)
		return () => removeEventListener('keydown', onKey)
	}, [tabs])

	const move = (to: number) => {
		const i = (to + tabs.length) % tabs.length
		setSelected(tabs[i].id)
		refs.current[i]?.focus()
	}

	return (
		<div className="flex flex-col gap-6">
			<div
				role="tablist"
				aria-label={label}
				className="flex gap-1.5 overflow-x-auto pb-0.5"
				onKeyDown={e => {
					const i = tabs.findIndex(t => t.id === selected)
					const to =
						e.key === 'ArrowRight'
							? i + 1
							: e.key === 'ArrowLeft'
								? i - 1
								: e.key === 'Home'
									? 0
									: e.key === 'End'
										? tabs.length - 1
										: null
					if (to === null) return
					e.preventDefault()
					move(to)
				}}
			>
				{tabs.map((tab, i) => {
					const on = tab.id === selected
					return (
						<button
							key={tab.id}
							ref={el => {
								refs.current[i] = el
							}}
							type="button"
							role="tab"
							id={`${base}-tab-${tab.id}`}
							aria-selected={on}
							aria-controls={`${base}-panel-${tab.id}`}
							tabIndex={on ? 0 : -1}
							onClick={() => setSelected(tab.id)}
							// Two blocks, terminal-style: the key, filled, then the label,
							// outlined. Selected, both fill with the foreground colour;
							// hover or keyboard focus fills the key and outlines the label.
							className="group flex h-[30px] shrink-0 items-stretch text-xs leading-[30px] tracking-[0.05em] whitespace-nowrap uppercase outline-none"
						>
							<kbd
								aria-hidden="true"
								className={cn(
									'min-w-[3ch] px-[1ch] text-center font-mono transition-colors duration-[120ms]',
									on
										? 'bg-foreground text-background'
										: 'bg-foreground/30 text-foreground group-hover:bg-foreground group-hover:text-background group-focus-visible:bg-foreground group-focus-visible:text-background'
								)}
							>
								{i + 1}
							</kbd>
							<span
								className={cn(
									'flex items-center gap-[1ch] px-[1.25ch] ring-1 transition-[background-color,color,box-shadow] duration-[120ms] ring-inset',
									on
										? 'bg-foreground text-background ring-foreground'
										: 'text-muted-foreground ring-foreground/30 group-hover:text-foreground group-hover:ring-foreground group-focus-visible:text-foreground group-focus-visible:ring-foreground'
								)}
							>
								{tab.label}
								{tab.count !== undefined && (
									<span className="tracking-normal normal-case opacity-65">
										{tab.count}
									</span>
								)}
							</span>
						</button>
					)
				})}
			</div>
			{tabs.map(tab => (
				<div
					key={tab.id}
					role="tabpanel"
					id={`${base}-panel-${tab.id}`}
					aria-labelledby={`${base}-tab-${tab.id}`}
					hidden={tab.id !== selected}
				>
					{tab.panel}
				</div>
			))}
		</div>
	)
}
