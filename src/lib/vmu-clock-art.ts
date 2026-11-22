import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import type { Animal, AnimalFrames, ClockArt } from './vmu-clock'

/** The US BIOS's clock pieces, read at build time from the archive's sprites. */
const DIR = path.join(process.cwd(), 'content/sprites/visual-memory-unit')

/** Each animal's two frames, by sprite file. The fish's are the same bytes. */
const ANIMAL_FILES: Record<Animal, [string, string]> = {
	dog: ['clock-dog-frame-1', 'clock-dog-frame-2'],
	fish: ['clock-fish', 'clock-fish'],
	bird: ['clock-bird-frame-1', 'clock-bird-frame-2']
}

interface SpriteFile {
	width: number
	height: number
	bpp: number
	frames: string[]
}

function read(name: string, width: number, height?: number): SpriteFile {
	const file = path.join(DIR, `${name}.json`)
	const sprite = JSON.parse(fs.readFileSync(file, 'utf8')) as SpriteFile
	if (
		sprite.bpp !== 1 ||
		sprite.width !== width ||
		(height !== undefined && sprite.height !== height)
	)
		throw new Error(
			`${file}: expected a 1-bit ${width}x${height ?? 'n'} sprite`
		)
	return sprite
}

export function getClockArt(): ClockArt {
	const font = read('big-font', 8)
	const animals = Object.fromEntries(
		Object.entries(ANIMAL_FILES).map(([animal, files]) => [
			animal,
			files.map(f => read(f, 8, 8).frames[0]) as unknown as AnimalFrames
		])
	) as Record<Animal, AnimalFrames>
	return { font: font.frames[0], glyphs: font.height / 8, animals }
}
