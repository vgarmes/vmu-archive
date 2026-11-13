'use client'

import { type ReactNode, useEffect, useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

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
 * between tabs (Base UI's tablist does that).
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

	return (
		<Tabs
			value={selected}
			onValueChange={value => setSelected(String(value))}
			className="gap-6"
		>
			{/* Scrolls sideways on a phone rather than squeezing the labels. */}
			<div className="-mx-4 overflow-x-auto px-4">
				<TabsList aria-label={label}>
					{tabs.map((tab, i) => (
						<TabsTrigger
							key={tab.id}
							value={tab.id}
							title={`${tab.label} (${i + 1})`}
						>
							{tab.label}
							{tab.count !== undefined && (
								<span className="font-mono tabular-nums opacity-60">
									{tab.count}
								</span>
							)}
						</TabsTrigger>
					))}
				</TabsList>
			</div>
			{tabs.map(tab => (
				<TabsContent key={tab.id} value={tab.id} keepMounted>
					{tab.panel}
				</TabsContent>
			))}
		</Tabs>
	)
}
