import type { Metadata, Viewport } from 'next'
import { Geist_Mono } from 'next/font/google'
import Link from 'next/link'
import Swirl from '@/components/Swirl'
import ThemeToggle from '@/components/ThemeToggle'
import './globals.css'

const geistMono = Geist_Mono({
	variable: '--font-geist-mono',
	subsets: ['latin']
})

const SITE = 'VMU Archive'

export const metadata: Metadata = {
	title: { default: SITE, template: `%s · ${SITE}` },
	description:
		'An archive of Dreamcast VMU screen art, searchable and free to download.',
	icons: { icon: '/favicon.svg' }
}

// Stops iOS Safari zooming into small inputs on focus; it still allows pinch-zoom.
export const viewport: Viewport = {
	width: 'device-width',
	initialScale: 1,
	maximumScale: 1
}

// Runs before first paint so the page never flashes the wrong theme.
const themeScript = `try{var t=localStorage.getItem('theme')||'auto';if(t==='dark'||(t==='auto'&&matchMedia('(prefers-color-scheme: dark)').matches))document.documentElement.classList.add('dark')}catch(e){}`

export default function RootLayout({ children }: LayoutProps<'/'>) {
	return (
		// The theme script adds a class before React hydrates.
		<html lang="en" className={geistMono.variable} suppressHydrationWarning>
			<head>
				<script dangerouslySetInnerHTML={{ __html: themeScript }} />
			</head>
			<body className="min-h-screen font-mono antialiased">
				<header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-6">
					<Link
						href="/"
						className="flex items-center gap-3 text-sm leading-none font-bold tracking-[0.2em] uppercase"
					>
						<Swirl className="h-4 w-auto shrink-0" />
						{SITE}
					</Link>
					<ThemeToggle />
				</header>
				<main className="mx-auto max-w-6xl px-4 pb-16">{children}</main>
			</body>
		</html>
	)
}
