'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from 'cn'
import { ArrowUpRightIcon } from 'lucide-react'
import ThemeToggle, { ThemeButtons } from '@/components/ThemeToggle'

type NavLink = { href: string; label: string; external?: boolean }

const LINKS: NavLink[] = [
	{ href: '/save-icons', label: 'Save icons' },
	{ href: '/about', label: 'About' },
	{ href: '/changelog', label: 'Changelog' },
	{
		href: 'https://github.com/vgarmes/vmu-archive',
		label: 'GitHub',
		external: true
	}
]

const NAV_LINK =
	'text-muted-foreground hover:bg-foreground hover:text-background focus-visible:bg-foreground focus-visible:text-background flex h-6 items-center gap-1 px-2 text-xs tracking-[0.2em] uppercase outline-none'

/** External links open in a new tab, marked with a diagonal arrow. */
const newTab = (external?: boolean) =>
	external ? { target: '_blank', rel: 'noreferrer' } : {}

function Label({ label, external }: NavLink) {
	return (
		<>
			{label}
			{external && <ArrowUpRightIcon aria-hidden className="size-3 shrink-0" />}
			{external && <span className="sr-only"> (opens in a new tab)</span>}
		</>
	)
}

/**
 * The header's links and theme. From `sm` up they sit in a row; below it they
 * fold into a menu that drops over the page under the header (the header must
 * be `relative`), with a scrim behind it. Overlaid rather than pushing the
 * page down, so opening it doesn't move what's under it.
 */
export default function SiteNav() {
	const [open, setOpen] = useState(false)
	const toggle = useRef<HTMLButtonElement>(null)
	const pathname = usePathname()

	// Close on navigation, including back/forward.
	useEffect(() => setOpen(false), [pathname])

	useEffect(() => {
		if (!open) return
		const onKey = (e: KeyboardEvent) => {
			if (e.key !== 'Escape') return
			setOpen(false)
			toggle.current?.focus()
		}
		// The menu only exists on phones; close it if the window grows past that.
		const wide = matchMedia('(min-width: 40rem)')
		const onWide = () => wide.matches && setOpen(false)
		document.addEventListener('keydown', onKey)
		wide.addEventListener('change', onWide)
		return () => {
			document.removeEventListener('keydown', onKey)
			wide.removeEventListener('change', onWide)
		}
	}, [open])

	return (
		<>
			<nav className="hidden items-center gap-4 sm:flex">
				{LINKS.map(link => (
					<Link
						key={link.href}
						href={link.href}
						className={NAV_LINK}
						{...newTab(link.external)}
					>
						<Label {...link} />
					</Link>
				))}
				{/*
					The links' px-2 only shows on hover, so their text sits 8px further
					apart than the toggle's border sits from its neighbour; this evens it.
				*/}
				<div className="ml-2">
					<ThemeToggle />
				</div>
			</nav>

			<button
				ref={toggle}
				type="button"
				aria-expanded={open}
				aria-controls="site-menu"
				aria-label={open ? 'Close menu' : 'Menu'}
				onClick={() => setOpen(o => !o)}
				className="text-muted-foreground hover:text-foreground focus-visible:ring-ring/50 relative -m-1 flex size-8 items-center justify-center outline-none focus-visible:ring-3 sm:hidden"
			>
				{/* Two bars that fold into an X. */}
				<span
					aria-hidden
					className={cn(
						'absolute h-px w-4 bg-current transition-transform duration-200 ease-out motion-reduce:transition-none',
						open ? 'rotate-45' : '-translate-y-[3px]'
					)}
				/>
				<span
					aria-hidden
					className={cn(
						'absolute h-px w-4 bg-current transition-transform duration-200 ease-out motion-reduce:transition-none',
						open ? '-rotate-45' : 'translate-y-[3px]'
					)}
				/>
			</button>

			<div
				aria-hidden
				onClick={() => setOpen(false)}
				className={cn(
					'absolute inset-x-0 top-full z-40 h-svh bg-black/50 transition-[opacity,visibility] duration-150 ease-out motion-reduce:transition-none sm:hidden',
					!open && 'invisible opacity-0'
				)}
			/>
			<div
				id="site-menu"
				inert={!open}
				className={cn(
					'bg-background absolute inset-x-0 top-full z-50 border-b px-4 pb-4 transition-[opacity,translate,visibility] duration-150 ease-out motion-reduce:transition-none sm:hidden',
					!open && 'invisible -translate-y-1 opacity-0'
				)}
			>
				<ul>
					{LINKS.map(link => (
						<li key={link.href} className="border-t">
							<Link
								href={link.href}
								onClick={() => setOpen(false)}
								aria-current={pathname === link.href ? 'page' : undefined}
								className="text-muted-foreground hover:text-foreground focus-visible:text-foreground aria-[current=page]:text-foreground flex h-12 items-center gap-1 text-xs tracking-[0.2em] uppercase outline-none"
								{...newTab(link.external)}
							>
								<Label {...link} />
							</Link>
						</li>
					))}
				</ul>
				<div className="flex items-center justify-between border-t pt-4">
					<span className="text-muted-foreground text-xs tracking-[0.2em] uppercase">
						Theme
					</span>
					<ThemeButtons />
				</div>
			</div>
		</>
	)
}
