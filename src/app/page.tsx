import GameIndex from '@/components/GameIndex'
import { getGames } from '@/lib/games'

export default function Home() {
	return (
		<>
			<section className="mb-8 flex flex-col gap-2">
				{/* Hidden visually; kept so the page still has a main heading. */}
				<h1 className="sr-only">Dreamcast VMU pixel art</h1>
				<p className="text-muted-foreground max-w-2xl text-sm">
					Screen art from the Dreamcast&apos;s Visual Memory Unit, game by game.
					Pick a game to browse its screens and download any of them as PNG,
					SVG, GIF or C source.
				</p>
			</section>
			<GameIndex games={getGames()} />
		</>
	)
}
