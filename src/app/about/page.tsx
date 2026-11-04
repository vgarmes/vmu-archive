import type { Metadata } from 'next'

export const metadata: Metadata = {
	title: 'About',
	description:
		'What the VMU Archive is, why it exists, and how to ask for a game that is missing.'
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
				<h1 className="text-sm font-normal tracking-[0.2em] uppercase">
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
				<h2 className="font-normal tracking-[0.2em] uppercase">
					Why it exists
				</h2>
				<p className="text-muted-foreground">
					Playing a Dreamcast for the first time, at my cousin&apos;s place in
					1999, is one of the highlights of my life as a gamer, and the
					impression it left has stayed with me ever since. It felt ahead of its
					time: it went online, and its graphics looked so real, considering I
					was still playing a PlayStation at home.
				</p>
				<p className="text-muted-foreground">
					Then there was the controller, and the attention to detail that went
					into it, above all the VMU: a memory card with its own LCD screen that
					plugged into the controller and showed different art depending on the
					game you were playing. It fascinated me.
				</p>
				<p className="text-muted-foreground">
					Years later I realized how little of that art had been preserved.
					Apart from a few games, like Sonic Adventure, whose VMU screens
					someone ripped and uploaded to{' '}
					<a
						href="https://www.spriters-resource.com/"
						className="hover:text-foreground underline underline-offset-4"
					>
						The Spriters Resource
					</a>
					, most of it wasn&apos;t anywhere. So I started this archive, to
					extract as much of it as I can from the games&apos; disc dumps.
				</p>
			</section>

			<section className="flex flex-col gap-3">
				<h2 className="font-normal tracking-[0.2em] uppercase">
					Request a game
				</h2>
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
