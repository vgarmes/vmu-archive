import type { Metadata } from 'next'

export const metadata: Metadata = {
	title: 'About',
	description:
		'What the VMU Archive is, and how to ask for a game that is missing.'
}

/** Where requests go. */
const CONTACT_EMAIL = 'vgmestre@gmail.com'

const SUBJECT = 'VMU Archive game request'
const BODY = `Game:
Region or release, if it matters (JP / US / EU):
VMU screens you remember (optional):`

const mailto = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(SUBJECT)}&body=${encodeURIComponent(BODY)}`

export default function About() {
	return (
		<article className="flex max-w-2xl flex-col gap-10 text-sm leading-6">
			<section className="flex flex-col gap-3">
				<h1 className="text-base font-bold tracking-[0.2em] uppercase">
					About
				</h1>
				<p className="text-muted-foreground">
					The Dreamcast&apos;s Visual Memory Unit has a tiny 48×32 pixel LCD
					that games used for everything from save icons to mini-games and
					in-game status screens. This archive collects that screen art, redrawn
					pixel for pixel, so it can be searched and downloaded as PNG, SVG, GIF
					or C source.
				</p>
			</section>

			<section className="flex flex-col gap-3">
				<h2 className="font-bold tracking-[0.2em] uppercase">Request a game</h2>
				<p className="text-muted-foreground">
					New screens come straight from each game&apos;s disc, with the order
					and timing its own code uses, so the archive grows a game at a time.
					Missing one you remember? Ask for it.
				</p>
				<ol className="text-muted-foreground flex list-decimal flex-col gap-2 pl-5">
					<li>Name the game, and the region or release if it matters.</li>
					<li>
						If you remember particular VMU screens (save menu, mini-game,
						boot…), mention them, so they can be checked once it&apos;s added.
					</li>
				</ol>
				<a
					href={mailto}
					className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 mt-2 self-start border px-4 py-2 uppercase"
				>
					Request a game
				</a>
			</section>
		</article>
	)
}
