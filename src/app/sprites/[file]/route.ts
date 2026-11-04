import { PNG } from 'pngjs'
import { LCD_INK } from '@/lib/pixels'
import { getSpriteGames, getSpriteSheet } from '@/lib/sprites'

/**
 * /sprites/<game slug>.png: every sprite of a game packed into one sheet (see
 * src/lib/sprites.ts), near-black on transparent like the thumbnails, so the
 * page can invert it in dark mode. Built with the site, never committed.
 */
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
	return getSpriteGames().map(game => ({ file: `${game}.png` }))
}

export async function GET(
	_req: Request,
	{ params }: RouteContext<'/sprites/[file]'>
) {
	const sheet = getSpriteSheet((await params).file.replace(/\.png$/, ''))
	if (!sheet) return new Response('Not found', { status: 404 })
	const png = new PNG({ width: sheet.width, height: sheet.height })
	png.data = Buffer.alloc(sheet.width * sheet.height * 4)
	sheet.pixels.forEach((lit, i) => {
		if (lit) png.data.set(LCD_INK, i * 4)
	})
	return new Response(
		new Uint8Array(PNG.sync.write(png, { colorType: 4, deflateLevel: 9 })),
		{
			headers: { 'Content-Type': 'image/png' }
		}
	)
}
