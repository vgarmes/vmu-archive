'use client'

import { Menu } from '@base-ui/react/menu'
import { useEffect, useMemo, useState } from 'react'
import {
	decodeFrame,
	LCD_INK,
	parseColor,
	toCArray,
	toHexColor,
	toRgba,
	toSvg,
	trimArt,
	type PixelArt
} from '@/lib/pixels'

/**
 * Large preview (animated when the art has several frames) and the download
 * menu. Every format is generated in the browser from the frame data, so
 * nothing but the JSON entry has to be stored per icon. The menu is Base UI's.
 */

const SCALES = [1, 4, 8, 16] as const
const DEFAULT_DELAY = 250

interface Props {
	id: string
	title: string
	art: PixelArt
}

export default function IconDetail({ id, title, art }: Props) {
	const [frame, setFrame] = useState(0)
	const [scale, setScale] = useState<number>(8)
	const [copied, setCopied] = useState(false)
	const [trim, setTrim] = useState(false)
	const lcd = art.bpp === 1
	const frames = art.frames.length

	useEffect(() => {
		if (frames < 2) return
		const t = setInterval(
			() => setFrame(f => (f + 1) % frames),
			art.frameDelayMs ?? DEFAULT_DELAY
		)
		return () => clearInterval(t)
	}, [frames, art.frameDelayMs])

	const preview = toSvg(art, {
		frame,
		style: lcd ? 'lcd' : 'flat',
		on: 'currentColor',
		off: 'color-mix(in srgb, currentColor 10%, transparent)',
		attrs: 'className="block h-auto w-full" aria-hidden="true"'
	})

	// Downloads use the trimmed art when asked; the C array never does, since
	// VMU code expects the whole 48x32 screen.
	const out = useMemo(() => (trim ? trimArt(art) : art), [art, trim])
	const name = trim ? `${id}-trimmed` : id
	const size = `${out.width * scale}×${out.height * scale}`
	const ink = toHexColor(LCD_INK)
	const downloads = [
		{
			label: 'PNG',
			detail: size,
			run: async () => save(await toPng(out, scale), `${name}@${scale}x.png`)
		},
		{
			label: 'SVG',
			detail: 'vector',
			run: () => save(svgBlob(toSvg(out, { on: ink })), `${name}.svg`)
		},
		...(lcd
			? [
					{
						label: 'SVG · LCD dots',
						detail: 'vector',
						run: () =>
							save(
								svgBlob(toSvg(out, { style: 'lcd', on: ink, off: `${ink}1f` })),
								`${name}-lcd.svg`
							)
					}
				]
			: []),
		{
			label: frames > 1 ? 'GIF (animated)' : 'GIF',
			detail: size,
			run: async () => save(await toGif(out, scale), `${name}@${scale}x.gif`)
		}
	]

	const copyC = async () => {
		await navigator.clipboard.writeText(toCArray(art, title))
		setCopied(true)
		setTimeout(() => setCopied(false), 1500)
	}

	return (
		<div className="grid gap-8 md:grid-cols-[3fr_2fr]">
			<div
				className="border-border bg-card flex items-center justify-center border p-6 sm:p-10"
				dangerouslySetInnerHTML={{ __html: preview }}
			/>

			<div className="flex flex-col gap-4">
				<h2 className="text-muted-foreground text-sm uppercase">Download</h2>
				<label className="flex items-center gap-3 text-sm">
					<span className="text-muted-foreground">Scale</span>
					<select
						value={scale}
						onChange={e => setScale(+e.currentTarget.value)}
						className="border-input bg-background border px-2 py-1"
					>
						{SCALES.map(s => (
							<option key={s} value={s}>
								{s}× ({out.width * s}×{out.height * s})
							</option>
						))}
					</select>
				</label>
				<label className="flex items-center gap-3 text-sm">
					<input
						type="checkbox"
						checked={trim}
						onChange={e => setTrim(e.currentTarget.checked)}
						className="accent-primary size-4"
					/>
					<span>Trim empty space</span>
				</label>
				<div className="flex flex-col gap-2">
					<Menu.Root>
						<Menu.Trigger className="border-primary hover:bg-primary hover:text-primary-foreground data-[popup-open]:bg-primary data-[popup-open]:text-primary-foreground flex items-center justify-between border px-4 py-2 text-sm uppercase">
							Download
							<span aria-hidden="true">▾</span>
						</Menu.Trigger>
						<Menu.Portal>
							<Menu.Positioner sideOffset={4} align="start">
								<Menu.Popup className="border-primary bg-background text-foreground w-(--anchor-width) border py-1 font-mono text-sm shadow-lg outline-none">
									{downloads.map(d => (
										<Menu.Item
											key={d.label}
											onClick={d.run}
											className="data-[highlighted]:bg-primary data-[highlighted]:text-primary-foreground flex cursor-pointer items-baseline justify-between gap-4 px-4 py-2 uppercase outline-none select-none"
										>
											{d.label}
											<span className="text-xs normal-case opacity-60">
												{d.detail}
											</span>
										</Menu.Item>
									))}
								</Menu.Popup>
							</Menu.Positioner>
						</Menu.Portal>
					</Menu.Root>
					<button
						type="button"
						onClick={copyC}
						className="border-border text-muted-foreground hover:text-foreground hover:border-foreground border px-4 py-2 text-left text-sm uppercase"
					>
						{copied ? 'Copied!' : 'Copy as C array'}
					</button>
				</div>
				{frames > 1 && (
					<p className="text-muted-foreground text-xs">
						{frames} frames. PNG and SVG export the first frame.
					</p>
				)}
			</div>
		</div>
	)
}

function save(blob: Blob, filename: string) {
	const url = URL.createObjectURL(blob)
	const a = Object.assign(document.createElement('a'), {
		href: url,
		download: filename
	})
	a.click()
	setTimeout(() => URL.revokeObjectURL(url), 1000)
}

const svgBlob = (svg: string) => new Blob([svg], { type: 'image/svg+xml' })

function toPng(art: PixelArt, scale: number): Promise<Blob> {
	const canvas = document.createElement('canvas')
	canvas.width = art.width * scale
	canvas.height = art.height * scale
	const data = new ImageData(
		toRgba(art, 0, scale) as Uint8ClampedArray<ArrayBuffer>,
		canvas.width,
		canvas.height
	)
	canvas.getContext('2d')!.putImageData(data, 0, 0)
	return new Promise((resolve, reject) =>
		canvas.toBlob(b => (b ? resolve(b) : reject()), 'image/png')
	)
}

/**
 * Our frames are already palette indices, so GIF needs no quantising.
 * gifenc is CommonJS and only needed on click, so it loads lazily.
 */
async function toGif(art: PixelArt, scale: number): Promise<Blob> {
	const { GIFEncoder } = await import('gifenc')
	const { width: w, height: h, bpp } = art
	const colors =
		bpp === 1 ? [[0, 0, 0, 0], LCD_INK] : art.palette!.map(parseColor)
	const palette = colors.map(([r, g, b]) => [r, g, b])
	const transparentIndex = colors.findIndex(c => c[3] === 0)
	const W = w * scale
	const H = h * scale

	const gif = GIFEncoder()
	for (const hex of art.frames) {
		const px = decodeFrame(hex, w, h, bpp)
		const big = new Uint8Array(W * H)
		for (let y = 0; y < H; y++)
			for (let x = 0; x < W; x++)
				big[y * W + x] = px[Math.floor(y / scale) * w + Math.floor(x / scale)]
		gif.writeFrame(big, W, H, {
			palette,
			delay: art.frameDelayMs ?? DEFAULT_DELAY,
			transparent: transparentIndex >= 0,
			transparentIndex: Math.max(0, transparentIndex)
		})
	}
	gif.finish()
	return new Blob([gif.bytes() as Uint8Array<ArrayBuffer>], {
		type: 'image/gif'
	})
}
