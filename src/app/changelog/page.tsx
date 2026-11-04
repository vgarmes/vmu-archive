import type { Metadata } from 'next'
import { getChangelogByDay } from '@/lib/changelog'

export const metadata: Metadata = {
	title: 'Changelog',
	description: 'New screens and other updates to the VMU Archive.'
}

const formatDate = (date: string) =>
	new Date(`${date}T00:00:00Z`).toLocaleDateString('en-US', {
		month: 'long',
		day: 'numeric',
		year: 'numeric',
		timeZone: 'UTC'
	})

export default function Changelog() {
	const days = getChangelogByDay()
	return (
		<article className="flex max-w-3xl flex-col gap-10 text-sm leading-6">
			<h1 className="text-sm font-normal tracking-[0.2em] uppercase">
				Changelog
			</h1>
			{/*
			 * From md up the dates sit in a column with a timeline on their left:
			 * each date and its dot stick to the top while their day scrolls past,
			 * and the next day's date pushes them out. The line runs 4px in from the
			 * left edge, through the dots' centres; a day's segment runs from its dot
			 * (or from its top, after the first) through the gap to the next day.
			 */}
			<ol className="flex flex-col gap-12">
				{days.map((day, i) => (
					<li
						key={day.date}
						className="relative grid gap-6 md:grid-cols-[11rem_1fr] md:gap-x-10 md:pl-6"
					>
						<span
							aria-hidden
							className={`bg-border absolute left-1 hidden w-px -translate-x-1/2 md:block ${
								i === 0 ? 'top-3' : 'top-0'
							} ${i === days.length - 1 ? 'bottom-0' : '-bottom-12'}`}
						/>
						<div className="relative md:sticky md:top-8 md:self-start">
							<time
								dateTime={day.date}
								className="text-muted-foreground block text-xs leading-6 tracking-[0.2em] uppercase"
							>
								{formatDate(day.date)}
							</time>
							<span
								aria-hidden
								className={`ring-background absolute top-3 -left-6 hidden size-2 -translate-y-1/2 ring-4 md:block ${
									i === 0 ? 'bg-dreamcast' : 'bg-muted-foreground'
								}`}
							/>
						</div>
						<ul className="flex flex-col gap-6">
							{day.entries.map(entry => (
								<li key={entry.title} className="flex flex-col gap-2">
									<h2 className="font-normal">{entry.title}</h2>
									{entry.body && (
										<p className="text-muted-foreground">{entry.body}</p>
									)}
								</li>
							))}
						</ul>
					</li>
				))}
			</ol>
		</article>
	)
}
