import { PNG } from 'pngjs'
import { getIcon, getIcons } from '@/lib/icons'
import { STRIP_GAP, toRgba } from '@/lib/pixels'

/**
 * A native-size PNG of each icon, a few hundred bytes each, at
 * /thumbs/<id>.png. The grid scales them up with `image-rendering: pixelated`.
 * The art is near-black on transparent; the page inverts it in dark mode.
 * Animations are a vertical strip of their frames (48x32 per frame, with
 * STRIP_GAP transparent rows between them), which the grid steps through on
 * hover and the drawer reads back.
 */
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
	return getIcons().map(icon => ({ file: `${icon.id}.png` }))
}

export async function GET(
	_req: Request,
	{ params }: RouteContext<'/thumbs/[file]'>
) {
	const icon = getIcon((await params).file.replace(/\.png$/, ''))
	if (!icon) return new Response('Not found', { status: 404 })
	const { data } = icon
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
