import { PNG } from 'pngjs'
import { getIcon, getIcons } from '@/lib/icons'
import { toRgba } from '@/lib/pixels'

/**
 * A native-size PNG of each icon's first frame, a few hundred bytes each, at
 * /thumbs/<id>.png. The grid scales them up with `image-rendering: pixelated`.
 * The art is near-black on transparent; the page inverts it in dark mode.
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
	const png = new PNG({ width: data.width, height: data.height })
	png.data = Buffer.from(toRgba(data))
	return new Response(new Uint8Array(PNG.sync.write(png)), {
		headers: { 'Content-Type': 'image/png' }
	})
}
