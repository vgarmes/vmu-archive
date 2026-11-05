import { GIFEncoder } from 'gifenc'
import { PNG } from 'pngjs'
import {
	colorsOf,
	decodeFrame,
	frameDelays,
	toRgba,
	type PixelArt
} from '@/lib/pixels'
import { getSaveIcon, getSaveIcons } from '@/lib/save-icons'

/**
 * /save-icons/<id>.png: the icon's first frame at native size (32x32), in its
 * own colours, which the page scales up with `image-rendering: pixelated`.
 * /save-icons/<id>.gif: the same, animated, for icons with more frames. The
 * header's animation speed isn't mapped to time yet, so the GIF plays at the
 * site's default delay.
 */
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
	return getSaveIcons().flatMap(icon => [
		{ file: `${icon.id}.png` },
		...(icon.frames > 1 ? [{ file: `${icon.id}.gif` }] : [])
	])
}

export async function GET(
	_req: Request,
	{ params }: RouteContext<'/save-icons/[file]'>
) {
	const file = (await params).file
	const icon = getSaveIcon(file.replace(/\.(png|gif)$/, ''))
	if (!icon) return new Response('Not found', { status: 404 })
	if (file.endsWith('.gif'))
		return new Response(new Uint8Array(toGif(icon.art)), {
			headers: { 'Content-Type': 'image/gif' }
		})
	const png = new PNG({ width: icon.art.width, height: icon.art.height })
	png.data = Buffer.from(toRgba(icon.art, 0))
	return new Response(new Uint8Array(PNG.sync.write(png)), {
		headers: { 'Content-Type': 'image/png' }
	})
}

/** The frames are palette indices already; a fully transparent colour stays so. */
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
