/**
 * Pixel art encoding shared by the importer (Node), the build and the browser.
 *
 * Every frame is stored as a hex string of packed palette indices, row-major:
 * - bpp 1 (VMU LCD, 48x32): 8 pixels per byte, leftmost pixel in the high bit.
 *   Index 0 is an unlit dot, 1 a lit one; the colours come from the theme.
 * - bpp 4 (save-file icons, 32x32): 2 pixels per byte, leftmost in the high
 *   nibble — the same layout as the bitmaps in a .VMS header.
 *
 * Keep this file free of imports and non-erasable TypeScript (enums etc.) so
 * Node can run it directly from scripts/import.ts.
 */

export type Bpp = 1 | 4

export interface PixelArt {
	width: number
	height: number
	bpp: Bpp
	/** "#rrggbbaa" per index; only for bpp 4. */
	palette?: string[]
	frames: string[]
	/** Delay between animation frames. */
	frameDelayMs?: number
}

export type Rgba = [number, number, number, number]

/** Hex chars a single frame takes (padded to whole bytes, for odd sprite sizes). */
export const frameHexLength = (w: number, h: number, bpp: Bpp) =>
	Math.ceil((w * h * bpp) / 8) * 2

export function decodeFrame(
	hex: string,
	width: number,
	height: number,
	bpp: Bpp
): Uint8Array {
	const out = new Uint8Array(width * height)
	const mask = (1 << bpp) - 1
	const perByte = 8 / bpp
	for (let i = 0; i < out.length; i++) {
		const byte = parseInt(
			hex.slice(Math.floor(i / perByte) * 2, Math.floor(i / perByte) * 2 + 2),
			16
		)
		const shift = 8 - bpp * ((i % perByte) + 1)
		out[i] = (byte >> shift) & mask
	}
	return out
}

export function encodeFrame(indices: ArrayLike<number>, bpp: Bpp): string {
	const perByte = 8 / bpp
	let hex = ''
	for (let i = 0; i < indices.length; i += perByte) {
		let byte = 0
		for (let j = 0; j < perByte; j++)
			byte = (byte << bpp) | ((indices[i + j] ?? 0) & ((1 << bpp) - 1))
		hex += byte.toString(16).padStart(2, '0')
	}
	return hex
}

export function parseColor(hex: string): Rgba {
	const v = hex.replace('#', '')
	const n = (i: number) => parseInt(v.slice(i, i + 2), 16)
	return [n(0), n(2), n(4), v.length >= 8 ? n(6) : 255]
}

export const toHexColor = ([r, g, b, a]: Rgba) =>
	'#' + [r, g, b, a].map(c => c.toString(16).padStart(2, '0')).join('')

/** Default inks for 1-bit art outside the page (downloads, thumbnails). */
export const LCD_INK: Rgba = [23, 23, 23, 255]
export const TRANSPARENT: Rgba = [0, 0, 0, 0]

/** The colour of every palette index. */
export function colorsOf(art: PixelArt, ink: Rgba = LCD_INK): Rgba[] {
	if (art.bpp === 1) return [TRANSPARENT, ink]
	return (art.palette ?? []).map(parseColor)
}

export const frameCount = (art: PixelArt) => art.frames.length

/** Delay between animation frames when an entry doesn't set one. */
export const DEFAULT_FRAME_DELAY_MS = 250

/**
 * Transparent rows between the frames of a thumbnail strip. Scaled up by a
 * non-integer factor, a frame's edge can land part-way through a screen pixel
 * and show a sliver of the next frame; with a gap, that sliver is empty.
 */
export const STRIP_GAP = 2

/**
 * The CSS object-position that shows one frame of a vertical thumbnail strip
 * (the image is one frame tall, object-fit: cover). Gaps between frames don't
 * change it: frame k is always k / (frames - 1) of the way down.
 */
export const stripPosition = (frames: number, frame = 0) =>
	`50% ${frames > 1 ? (frame / (frames - 1)) * 100 : 0}%`

export interface SvgOptions {
	frame?: number
	/** "flat": crisp square pixels. "lcd": VMU dot matrix with gaps. */
	style?: 'flat' | 'lcd'
	/** Fill for lit 1-bit pixels; any CSS colour (e.g. "currentColor"). */
	on?: string
	/** Fill for unlit dots in "lcd" style; omit to leave them out. */
	off?: string
	/** Fill behind everything (the screen colour); omit for transparent. */
	background?: string
	/** Draw the unlit dots only inside this area, e.g. to show a trim. */
	offBox?: Box
	/** Extra attributes for the root element, e.g. 'class="w-full"'. */
	attrs?: string
}

/** An area of the art, in pixels. */
export interface Box {
	x: number
	y: number
	width: number
	height: number
}

/**
 * The art as SVG. Flat style merges horizontal runs of one colour into a
 * single rectangle, so a typical icon is a few hundred path commands rather
 * than one per pixel.
 */
export function toSvg(art: PixelArt, opts: SvgOptions = {}): string {
	const { frame = 0, style = 'flat', on = toHexColor(LCD_INK) } = opts
	return svgDocument(
		art.width,
		art.height,
		svgPaths(art, frame, style, on),
		opts
	)
}

/**
 * Every frame side by side, frame 1 at the left, each in its own
 * <g id="frame-N"> so design tools show the frames as separate groups.
 */
export function toSvgSheet(
	art: PixelArt,
	opts: Omit<SvgOptions, 'frame'> = {}
): string {
	const { style = 'flat', on = toHexColor(LCD_INK) } = opts
	const body = art.frames
		.map((_, f) => {
			const move = f ? ` transform="translate(${f * art.width} 0)"` : ''
			return `<g id="frame-${f + 1}"${move}>${svgPaths(art, f, style, on)}</g>`
		})
		.join('')
	return svgDocument(art.width * art.frames.length, art.height, body, opts)
}

/**
 * An animation as one SVG that plays itself, e.g. in an <img> on any page.
 * Each distinct frame is drawn once in <defs>; a <use> per stored frame shows
 * it for one delay, so repeated frames (held longer) cost a line, not a copy.
 * CSS does the timing: every frame loops with the same cycle, visible for its
 * slot only, offset by its position. With reduced motion it shows frame 1.
 * Names are prefixed because CSS in an SVG inlined into HTML is page-wide.
 */
export function toAnimatedSvg(
	art: PixelArt,
	opts: Omit<SvgOptions, 'frame'> = {}
): string {
	const n = art.frames.length
	if (n < 2) return toSvg(art, opts)
	const { style = 'flat', on = toHexColor(LCD_INK) } = opts
	const delay = art.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS
	const distinct = distinctFrames(art)
	const drawn = distinct
		.map(
			(f, k) => `<g id="vmu-frame-${k + 1}">${svgPaths(art, f, style, on)}</g>`
		)
		.join('')
	const uses = art.frames
		.map((hex, i) => {
			const k = distinct.indexOf(art.frames.indexOf(hex)) + 1
			return `<use class="vmu-f vmu-f${i + 1}" href="#vmu-frame-${k}"/>`
		})
		.join('')
	const slot = +(100 / n).toFixed(4)
	const css =
		`.vmu-f{visibility:hidden;animation:vmu-frame ${n * delay}ms step-end infinite}` +
		art.frames
			.slice(1)
			.map((_, i) => `.vmu-f${i + 2}{animation-delay:${(i + 1) * delay}ms}`)
			.join('') +
		`@keyframes vmu-frame{0%{visibility:visible}${slot}%{visibility:hidden}}` +
		`@media (prefers-reduced-motion:reduce){.vmu-f{animation:none}.vmu-f1{visibility:visible}}`
	return svgDocument(art.width, art.height, uses, opts, {
		css,
		defs: drawn,
		rootAttrs: `data-frames="${n}" data-frame-delay-ms="${delay}"`
	})
}

const lcdGap = (style: SvgOptions['style']) => (style === 'lcd' ? 0.12 : 0)

/** One frame's pixels as <path>s, one per colour, in pixel units. */
function svgPaths(
	art: PixelArt,
	frame: number,
	style: SvgOptions['style'],
	on: string
): string {
	const { width: w, height: h, bpp } = art
	const px = decodeFrame(art.frames[frame], w, h, bpp)
	const fills = bpp === 1 ? ['', on] : (art.palette ?? []).map(svgFill)
	const paths = new Map<number, string>()
	const add = (idx: number, d: string) =>
		paths.set(idx, (paths.get(idx) ?? '') + d)

	const dot = +(1 - lcdGap(style)).toFixed(2)

	for (let y = 0; y < h; y++) {
		let x = 0
		while (x < w) {
			const idx = px[y * w + x]
			let run = 1
			if (style === 'flat')
				while (x + run < w && px[y * w + x + run] === idx) run++
			if (isVisible(art, idx)) {
				const len = style === 'flat' ? run : dot
				add(idx, `M${x} ${y}h${len}v${dot}h-${len}z`)
			}
			x += run
		}
	}

	let body = ''
	for (const [idx, d] of paths) body += `<path fill="${fills[idx]}" d="${d}"/>`
	return body
}

/**
 * The <svg> around some paths: the unlit-dot grid for "lcd", and the size.
 * `extra` adds a <style>, more <defs> and root attributes (animated export).
 */
function svgDocument(
	w: number,
	h: number,
	paths: string,
	{ style = 'flat', off, offBox, background, attrs }: SvgOptions,
	extra: { css?: string; defs?: string; rootAttrs?: string } = {}
): string {
	const gap = lcdGap(style)
	const dot = +(1 - gap).toFixed(2)
	const viewBox = `0 0 ${w - gap} ${h - gap}`
	let defs = extra.defs ?? ''
	// The screen colour, like the dots limited to `offBox` when there is one,
	// and ending at the last dot's edge as the viewBox does.
	const screen = background
		? offBox
			? `<rect x="${offBox.x}" y="${offBox.y}" width="${+(offBox.width - gap).toFixed(2)}" height="${+(offBox.height - gap).toFixed(2)}" fill="${background}"/>`
			: `<rect width="100%" height="100%" fill="${background}"/>`
		: ''
	let grid = ''
	if (style === 'lcd' && off) {
		// Fixed, not random: the server and browser renders must match, and
		// there's only ever one preview per page.
		const id = 'vmu-dots'
		defs =
			`<pattern id="${id}" width="1" height="1" patternUnits="userSpaceOnUse">` +
			`<rect width="${dot}" height="${dot}" fill="${off}"/></pattern>` +
			defs
		grid = offBox
			? `<rect x="${offBox.x}" y="${offBox.y}" width="${offBox.width}" height="${offBox.height}" fill="url(#${id})"/>`
			: `<rect width="100%" height="100%" fill="url(#${id})"/>`
	}
	const body =
		(extra.css ? `<style>${extra.css}</style>` : '') +
		(defs ? `<defs>${defs}</defs>` : '') +
		screen +
		grid +
		paths

	const root =
		(extra.rootAttrs ? ` ${extra.rootAttrs}` : '') + (attrs ? ` ${attrs}` : '')
	return (
		`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" ` +
		`width="${w * 8}" height="${h * 8}" shape-rendering="crispEdges"${root}>` +
		body +
		`</svg>`
	)
}

function isVisible(art: PixelArt, idx: number) {
	if (art.bpp === 1) return idx === 1
	const color = art.palette?.[idx]
	return !!color && parseColor(color)[3] > 0
}

/**
 * The smallest box that holds every visible pixel. One box covers all frames,
 * so an animation stays aligned. Null for blank art.
 */
export function trimBox(art: PixelArt): Box | null {
	const { width: w, height: h, bpp } = art
	let x0 = w,
		y0 = h,
		x1 = -1,
		y1 = -1
	for (const hex of art.frames) {
		const px = decodeFrame(hex, w, h, bpp)
		for (let y = 0; y < h; y++)
			for (let x = 0; x < w; x++)
				if (isVisible(art, px[y * w + x])) {
					x0 = Math.min(x0, x)
					y0 = Math.min(y0, y)
					x1 = Math.max(x1, x)
					y1 = Math.max(y1, y)
				}
	}
	if (x1 < 0) return null
	return { x: x0, y: y0, width: x1 - x0 + 1, height: y1 - y0 + 1 }
}

/** The art cropped to its `trimBox`. Blank art is returned as is. */
export function trimArt(art: PixelArt): PixelArt {
	const box = trimBox(art)
	if (!box) return art
	const { width: w, height: h, bpp } = art
	const { x: x0, y: y0, width, height } = box
	const decoded = art.frames.map(hex => decodeFrame(hex, w, h, bpp))
	const frames = decoded.map(px => {
		const out = new Uint8Array(width * height)
		for (let y = 0; y < height; y++)
			for (let x = 0; x < width; x++)
				out[y * width + x] = px[(y + y0) * w + x + x0]
		return encodeFrame(out, bpp)
	})
	return { ...art, width, height, frames }
}

/**
 * Indices of the frames that differ from every earlier one. An animation can
 * repeat a frame to hold it longer (Puck is 1, 2, 3, 3), which a frame picker
 * shouldn't list twice.
 */
export const distinctFrames = (art: PixelArt) =>
	art.frames.flatMap((hex, i) => (art.frames.indexOf(hex) === i ? [i] : []))

/** One frame of an animation as a still. */
export const withFrame = (art: PixelArt, frame: number): PixelArt => ({
	...art,
	frames: [art.frames[frame]],
	frameDelayMs: undefined
})

/** Every frame side by side, frame 1 at the left, as one still (a sprite sheet). */
export function toSheet(art: PixelArt): PixelArt {
	const { width: w, height: h, bpp } = art
	const n = art.frames.length
	const out = new Uint8Array(w * n * h)
	art.frames.forEach((hex, f) => {
		const px = decodeFrame(hex, w, h, bpp)
		for (let y = 0; y < h; y++)
			for (let x = 0; x < w; x++) out[y * w * n + f * w + x] = px[y * w + x]
	})
	return {
		...art,
		width: w * n,
		frames: [encodeFrame(out, bpp)],
		frameDelayMs: undefined
	}
}

function svgFill(hex: string) {
	const [r, g, b, a] = parseColor(hex)
	return a === 255
		? `rgb(${r},${g},${b})`
		: `rgba(${r},${g},${b},${+(a / 255).toFixed(3)})`
}

/** RGBA bytes for one frame, each pixel scaled up to a `scale`-sized block. */
export function toRgba(
	art: PixelArt,
	frame = 0,
	scale = 1,
	ink: Rgba = LCD_INK
): Uint8ClampedArray {
	const { width: w, height: h, bpp } = art
	const px = decodeFrame(art.frames[frame], w, h, bpp)
	const colors = colorsOf(art, ink)
	const W = w * scale
	const out = new Uint8ClampedArray(W * h * scale * 4)
	for (let y = 0; y < h * scale; y++) {
		for (let x = 0; x < W; x++) {
			const c =
				colors[px[Math.floor(y / scale) * w + Math.floor(x / scale)]] ??
				TRANSPARENT
			out.set(c, (y * W + x) * 4)
		}
	}
	return out
}

/** The frames as a C source snippet, for VMU homebrew. */
export function toCArray(art: PixelArt, name: string): string {
	const ident =
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '_')
			.replace(/^_|_$/g, '') || 'icon'
	const bytesPerFrame = frameHexLength(art.width, art.height, art.bpp) / 2
	const lines = [
		`/* ${name}: ${art.width}x${art.height}, ${art.bpp}bpp, ${art.frames.length} frame(s) */`
	]
	if (art.bpp === 4 && art.palette) {
		// VMS headers store colours as ARGB4444.
		const argb = art.palette.map(c => {
			const [r, g, b, a] = parseColor(c).map(v => v >> 4)
			return (
				'0x' +
				((a << 12) | (r << 8) | (g << 4) | b).toString(16).padStart(4, '0')
			)
		})
		lines.push(
			`const unsigned short ${ident}_palette[16] = { ${argb.join(', ')} };`
		)
	}
	lines.push(
		`const unsigned char ${ident}[${art.frames.length}][${bytesPerFrame}] = {`
	)
	for (const hex of art.frames) {
		const bytes = hex.match(/../g)!.map(b => '0x' + b)
		const rows: string[] = []
		for (let i = 0; i < bytes.length; i += 12)
			rows.push('\t\t' + bytes.slice(i, i + 12).join(', '))
		lines.push('\t{\n' + rows.join(',\n') + '\n\t},')
	}
	lines.push('};')
	return lines.join('\n')
}
