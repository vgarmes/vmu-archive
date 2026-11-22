/**
 * The VMU's clock screen, as the US BIOS v1.05 draws it (see the clock
 * sections of content/games/visual-memory-unit.md and gyrovorbis's
 * disassembly, `american_v1.05.s`). Everything is drawn from the archive's
 * own sprites: the big font and the clock animals.
 *
 * Time (`ClockMode` $1034, `ClockDrawTime` $10CA): HH:MM in the big font on
 * the top row of 8x8 cells. Column 0 is blank, the hour is 24-hour with no
 * leading zero (a blank cell, then the digit, below 10), then ":" and the
 * minutes, always two digits. The rest of the top half stays blank.
 *
 * Animal (`ClockAnimationStep` $1805): one step whenever the clock's second
 * changes. A pass walks the animal through its six positions, alternating
 * its two frames and leaving each one drawn, so a trail builds up; the next
 * pass walks the blank sprite through the same positions, wiping them. A
 * redraw of the screen (coming back from the date, picking an animal)
 * starts it over on an empty half.
 *
 * Date (`ClockShowDate` $112E): the day and the month's three letters on the
 * top row, the year two rows down. No animal.
 */

export const ANIMALS = ['dog', 'fish', 'bird'] as const
export type Animal = (typeof ANIMALS)[number]

/** A sprite's two frames, 8x8, as the archive stores them (hex). */
export type AnimalFrames = readonly [string, string]

export interface ClockArt {
	/** The big font, 8 wide, its 8x8 characters one under the next (hex). */
	font: string
	/** Characters in the font. */
	glyphs: number
	animals: Record<Animal, AnimalFrames>
}

export const WIDTH = 48
export const HEIGHT = 32
const CELL = 8

/**
 * `AnimSequences` ($1907): each animal's six positions as offsets into the
 * lower half's screen memory (XRAM bank 1), as the ROM holds them.
 */
const SEQUENCES: Record<Animal, readonly number[]> = {
	dog: [0x86, 0x91, 0x98, 0xa3, 0xaa, 0xb5],
	fish: [0x90, 0xa1, 0x92, 0xa3, 0x94, 0xa5],
	bird: [0xb0, 0xa1, 0xa2, 0x93, 0x94, 0x85]
}

/**
 * An XRAM offset in the lower half to its top-left pixel. Each 16 bytes hold
 * two 6-byte lines of 48 dots, a byte being 8 dots across.
 */
function xramXY(offset: number): [number, number] {
	const pair = (offset & 0x7f) >> 4
	const r = offset & 0x0f
	return [(r % 6) * CELL, HEIGHT / 2 + pair * 2 + Math.floor(r / 6)]
}

/** The steps in one cycle: a drawing pass and a wiping pass of six. */
export const CYCLE_STEPS = 12

/** The big font's ":" and where its letters start (ASCII minus $31). */
const COLON = 0x0a
const letter = (c: string) => c.charCodeAt(0) - 0x31

const MONTHS = [
	'JAN',
	'FEB',
	'MAR',
	'APR',
	'MAY',
	'JUN',
	'JUL',
	'AUG',
	'SEP',
	'OCT',
	'NOV',
	'DEC'
]

/** Bits of an 8-dot-wide image (hex), 0/1 per dot, row-major. */
function bits(hex: string, height: number): Uint8Array {
	const out = new Uint8Array(CELL * height)
	for (let y = 0; y < height; y++) {
		const byte = parseInt(hex.slice(y * 2, y * 2 + 2), 16)
		for (let x = 0; x < CELL; x++) out[y * CELL + x] = (byte >> (7 - x)) & 1
	}
	return out
}

/** Copies an 8x8 image into the screen at (x, y), replacing what was there. */
function blit(screen: Uint8Array, sprite: Uint8Array, x: number, y: number) {
	for (let row = 0; row < CELL; row++)
		for (let col = 0; col < CELL; col++)
			screen[(y + row) * WIDTH + x + col] = sprite[row * CELL + col]
}

export interface ClockScreen {
	view: 'time' | 'date'
	now: Date
	animal: Animal
	/** Animation steps since the screen was last drawn. */
	steps: number
}

/** Builds a screen's dots, 0/1, row-major, 48x32. */
export function makeClockDrawer(art: ClockArt) {
	const font = bits(art.font, art.glyphs * CELL)
	const glyph = (n: number) => font.subarray(n * 64, n * 64 + 64)
	const sprites = Object.fromEntries(
		ANIMALS.map(a => [a, art.animals[a].map(f => bits(f, CELL))])
	) as Record<Animal, Uint8Array[]>

	/** Draws a big-font glyph into a cell of the 6x4 grid. */
	const cell = (screen: Uint8Array, n: number, col: number, row: number) =>
		blit(screen, glyph(n), col * CELL, row * CELL)
	/** A number below 100 at `col`: blank and one digit below 10, as the BIOS. */
	const number = (screen: Uint8Array, n: number, col: number, row: number) => {
		if (n >= 10) cell(screen, Math.floor(n / 10), col, row)
		cell(screen, n % 10, col + 1, row)
	}

	return function draw({ view, now, animal, steps }: ClockScreen) {
		const screen = new Uint8Array(WIDTH * HEIGHT)
		if (view === 'date') {
			number(screen, now.getDate(), 0, 0)
			MONTHS[now.getMonth()]
				.split('')
				.forEach((c, i) => cell(screen, letter(c), 3 + i, 0))
			String(now.getFullYear())
				.padStart(4, '0')
				.slice(-4)
				.split('')
				.forEach((d, i) => cell(screen, Number(d), 2 + i, 2))
			return screen
		}

		number(screen, now.getHours(), 1, 0)
		cell(screen, COLON, 3, 0)
		const minutes = now.getMinutes()
		cell(screen, Math.floor(minutes / 10), 4, 0)
		cell(screen, minutes % 10, 5, 0)

		// Where the cycle is after `steps` steps: positions drawn so far in a
		// drawing pass, or wiped so far in a wiping one (wiped means blank).
		if (steps > 0) {
			const step = (steps - 1) % CYCLE_STEPS
			const wiping = step >= CYCLE_STEPS / 2
			const reached = (step % (CYCLE_STEPS / 2)) + 1
			SEQUENCES[animal].forEach((offset, i) => {
				const drawn = wiping ? i >= reached : i < reached
				if (!drawn) return
				const [x, y] = xramXY(offset)
				blit(screen, sprites[animal][i % 2], x, y)
			})
		}
		return screen
	}
}

/** The strip's size: the bird's path, then the screen's time row, side by side. */
export const STRIP_WIDTH = WIDTH * 2
/** The bird climbs 6 dots over its path, above the 8-dot row it starts on. */
const BIRD_CLIMB = 6
export const STRIP_HEIGHT = CELL + BIRD_CLIMB

/**
 * The site footer's clock: the bird's six positions as the screen's lower
 * half holds them, at the left, and the time row exactly as the screen draws
 * it at the right (its blank first column the gap between them). The rows
 * are lined up so the bird's lowest position sits level with the digits: it
 * takes off from the time. Steps as `makeClockDrawer`'s.
 */
export function makeClockStripDrawer(art: ClockArt) {
	const draw = makeClockDrawer(art)
	// The bird's rows on the screen: its highest position's top to its lowest's bottom.
	const ys = SEQUENCES.bird.map(o => xramXY(o)[1])
	const top = Math.min(...ys)
	const bottom = Math.max(...ys) + CELL

	return function drawStrip({ now, steps }: { now: Date; steps: number }) {
		const screen = draw({ view: 'time', now, animal: 'bird', steps })
		const strip = new Uint8Array(STRIP_WIDTH * STRIP_HEIGHT)
		const copy = (fromY: number, toY: number, toX: number) => {
			const row = screen.subarray(fromY * WIDTH, fromY * WIDTH + WIDTH)
			strip.set(row, toY * STRIP_WIDTH + toX)
		}
		for (let y = top; y < bottom; y++) copy(y, y - top, 0)
		for (let y = 0; y < CELL; y++) copy(y, STRIP_HEIGHT - CELL + y, WIDTH)
		return strip
	}
}

/** What the screen says, for a screen reader. */
export function describeClock({ view, now, animal }: ClockScreen) {
	if (view === 'date')
		return `${now.getDate()} ${MONTHS[now.getMonth()]} ${now.getFullYear()}`
	const mm = String(now.getMinutes()).padStart(2, '0')
	return `${now.getHours()}:${mm}, with the ${animal} walking below`
}
