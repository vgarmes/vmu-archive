import type { Metadata } from 'next'

export const metadata: Metadata = {
	title: 'About',
	description:
		'What the VMU Archive is, and how to send in VMU screen art that is missing.'
}

/** Where submissions go. */
const CONTACT_EMAIL = 'vgmestre@gmail.com'

const SUBJECT = 'VMU Archive submission'
const BODY = `Game:
Region (JP / US / EU):
Where the screen appears (save menu, mini-game, boot…):
Animated? (yes / no):

Screenshots attached.`

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
				<h2 className="font-bold tracking-[0.2em] uppercase">Contribute</h2>
				<p className="text-muted-foreground">
					Missing a screen you remember? Email a screenshot and it will be added
					to the archive.
				</p>
				<ol className="text-muted-foreground flex list-decimal flex-col gap-2 pl-5">
					<li>
						Capture the VMU screen in an emulator such as Flycast, or take a
						sharp, straight-on photo of a real VMU.
					</li>
					<li>
						Crop to the VMU display if you can. A full window is fine too. PNG
						is best.
					</li>
					<li>
						For animations, send one screenshot per frame, or a short screen
						recording.
					</li>
					<li>
						Say which game it&apos;s from, the region, and where the screen
						appears (save menu, mini-game, boot…).
					</li>
				</ol>
				<a
					href={mailto}
					className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 mt-2 self-start border px-4 py-2 uppercase"
				>
					Email a submission
				</a>
			</section>
		</article>
	)
}
