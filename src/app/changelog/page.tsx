import type { Metadata } from 'next'
import { getChangelog } from '@/lib/changelog'

export const metadata: Metadata = {
	title: 'Changelog',
	description: 'New screens and other updates to the VMU Archive.'
}

const formatDate = (date: string) =>
	new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', {
		day: 'numeric',
		month: 'long',
		year: 'numeric',
		timeZone: 'UTC'
	})

export default function Changelog() {
	return (
		<article className="flex max-w-2xl flex-col gap-10 text-sm leading-6">
			<h1 className="text-sm font-normal tracking-[0.2em] uppercase">
				Changelog
			</h1>
			<ol className="flex flex-col gap-10">
				{getChangelog().map(entry => (
					<li
						key={`${entry.date}-${entry.title}`}
						className="flex flex-col gap-2"
					>
						<time
							dateTime={entry.date}
							className="text-muted-foreground text-xs tracking-[0.2em] uppercase"
						>
							{formatDate(entry.date)}
						</time>
						<h2 className="font-normal">{entry.title}</h2>
						{entry.body && (
							<p className="text-muted-foreground">{entry.body}</p>
						)}
					</li>
				))}
			</ol>
		</article>
	)
}
