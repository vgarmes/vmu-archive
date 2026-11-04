import { GIFEncoder } from 'gifenc'
import { PNG } from 'pngjs'
import { getIcon, getIcons } from '@/lib/icons'
import {
	colorsOf,
	decodeFrame,
	frameDelays,
	gifFrames,
	scrollStripSize,
	STRIP_GAP,
	toRgba,
	type PixelArt
} from '@/lib/pixels'

/**
 * Native-size thumbnails of each icon, a few hundred bytes each, which the
 * grid scales up with `image-rendering: pixelated`. The art is near-black on
 * transparent; the page inverts it in dark mode.
 * - /thumbs/<id>.png: the icon, or for an animation a vertical strip of its
 *   frames (48x32 each, with STRIP_GAP transparent rows between them). The
 *   grid shows it cropped to the poster frame; the drawer reads it back. For a
 *   scroll it's the stored strip itself: the grid shows its start (left end,
 *   or bottom end for a "down" scroll), and the drawer cuts the frames from it.
 * - /thumbs/<id>.gif: animations only, played in the grid on hover. Every
 *   frame is the whole image, so it can be scaled to any size without art
 *   that stays put between frames shifting by a pixel (stepping through the
 *   strip instead made it jump).
 */
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
	return getIcons().flatMap(icon => [
		{ file: `${icon.id}.png` },
		...(icon.data.frames.length > 1 ? [{ file: `${icon.id}.gif` }] : [])
	])
}

export async function GET(
	_req: Request,
	{ params }: RouteContext<'/thumbs/[file]'>
) {
	const file = (await params).file
	const icon = getIcon(file.replace(/\.(png|gif)$/, ''))
	if (!icon) return new Response('Not found', { status: 404 })
	const { data } = icon
	if (file.endsWith('.gif'))
		return new Response(new Uint8Array(toGif(gifFrames(data, !!data.scroll))), {
			headers: { 'Content-Type': 'image/gif' }
		})

	if (data.scroll) {
		const strip = {
			...data,
			...scrollStripSize(data.scroll, data.width, data.height),
			frames: [data.scroll.strip]
		}
		const png = new PNG({ width: strip.width, height: strip.height })
		png.data = Buffer.from(toRgba(strip, 0))
		return new Response(new Uint8Array(PNG.sync.write(png)), {
			headers: { 'Content-Type': 'image/png' }
		})
	}

	const n = data.frames.length
	const pitch = data.height + STRIP_GAP
	const png = new PNG({
		width: data.width,
		height: n * data.height + (n - 1) * STRIP_GAP
	})
	png.data = Buffer.alloc(png.width * png.height * 4)
	data.frames.forEach((_, f) =>
		png.data.set(toRgba(data, f), f * pitch * data.width * 4)
	)
	return new Response(new Uint8Array(PNG.sync.write(png)), {
		headers: { 'Content-Type': 'image/png' }
	})
}

/** The frames are already palette indices, so the GIF needs no quantising. */
function toGif(art: PixelArt) {
	const { width: w, height: h, bpp } = art
	const colors = colorsOf(art)
	const palette = colors.map(([r, g, b]) => [r, g, b])
	const transparentIndex = colors.findIndex(c => c[3] === 0)
	const delays = frameDelays(art)
	const gif = GIFEncoder()
	art.frames.forEach((hex, f) =>
		gif.writeFrame(decodeFrame(hex, w, h, bpp), w, h, {
			palette,
			delay: delays[f],
			transparent: transparentIndex >= 0,
			transparentIndex: Math.max(0, transparentIndex)
		})
	)
	gif.finish()
	return gif.bytes()
}
