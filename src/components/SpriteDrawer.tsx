'use client'

import { useEffect, useMemo, useState } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import {
	Drawer,
	DrawerContent,
	DrawerDescription,
	DrawerFooter,
	DrawerHeader,
	DrawerTitle
} from '@/components/ui/drawer'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue
} from '@/components/ui/Select'
import type { IndexEntry } from '@/lib/icons'
import {
	decodeFrame,
	encodeFrame,
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
 * The sprite drawer: a large preview and the export options. It slides in
 * from the right on desktop and up from the bottom, with a swipe handle, on
 * smaller screens.
 *
 * No extra data is fetched: the pixels are read back from the thumbnail the
 * grid already loaded (a native 48x32 PNG where opaque means lit), and every
 * export is generated in the browser from them. Animated sprites aren't
 * supported yet — only the first frame is in the thumbnail.
 */

const SCALES = [1, 4, 8, 16]
const DEFAULT_DELAY = 250
/** Above this width the drawer is a side panel rather than a bottom sheet. */
const DESKTOP = '(min-width: 768px)'

type Format = 'png' | 'svg' | 'svg-lcd' | 'gif'

/** Sprites already read from their thumbnails this visit, by icon id. */
const artCache = new Map<string, PixelArt>()

function useIsDesktop() {
	const [desktop, setDesktop] = useState(false)
	useEffect(() => {
		const media = matchMedia(DESKTOP)
		const update = () => setDesktop(media.matches)
		update()
		media.addEventListener('change', update)
		return () => media.removeEventListener('change', update)
	}, [])
	return desktop
}

/** The sprite's pixels, read from its (already cached) thumbnail. */
function useThumbnailArt(id: string) {
	const [read, setRead] = useState<{ id: string; art: PixelArt } | null>(null)
	useEffect(() => {
		const cached = artCache.get(id)
		if (cached) return setRead({ id, art: cached })
		let cancelled = false
		const img = new Image()
		img.onload = () => {
			const canvas = document.createElement('canvas')
			canvas.width = 48
			canvas.height = 32
			const ctx = canvas.getContext('2d')!
			ctx.drawImage(img, 0, 0)
			const { data } = ctx.getImageData(0, 0, 48, 32)
			const bits = Array.from({ length: 48 * 32 }, (_, i) =>
				data[i * 4 + 3] >= 128 ? 1 : 0
			)
			const art: PixelArt = {
				width: 48,
				height: 32,
				bpp: 1,
				frames: [encodeFrame(bits, 1)]
			}
			artCache.set(id, art)
			if (!cancelled) setRead({ id, art })
		}
		img.src = `/thumbs/${id}.png`
		return () => {
			cancelled = true
		}
	}, [id])
	return read && read.id === id ? read.art : null
}

interface Props {
	/** The sprite to show; null closes the drawer. */
	entry: IndexEntry | null
	onClose: () => void
}

export default function SpriteDrawer({ entry, onClose }: Props) {
	const desktop = useIsDesktop()
	// Keep showing the last sprite while the drawer animates closed.
	const [shown, setShown] = useState<IndexEntry | null>(entry)
	useEffect(() => {
		if (entry) setShown(entry)
	}, [entry])

	return (
		<Drawer
			open={entry !== null}
			onOpenChange={open => {
				if (!open) onClose()
			}}
			swipeDirection={desktop ? 'right' : 'down'}
			showSwipeHandle={!desktop}
		>
			<DrawerContent>
				{shown && <SpritePanel key={shown.id} entry={shown} />}
			</DrawerContent>
		</Drawer>
	)
}

function SpritePanel({ entry }: { entry: IndexEntry }) {
	const art = useThumbnailArt(entry.id)
	const [scale, setScale] = useState<number>(8)
	const [copied, setCopied] = useState(false)
	const [trim, setTrim] = useState(false)
	const [format, setFormat] = useState<Format>('png')

	const preview = art
		? toSvg(art, {
				style: 'lcd',
				on: 'currentColor',
				off: 'color-mix(in srgb, currentColor 10%, transparent)',
				attrs: 'class="block h-auto w-full" aria-hidden="true"'
			})
		: null

	// Downloads use the trimmed art when asked; the C array never does, since
	// VMU code expects the whole 48x32 screen.
	const out = useMemo(() => (art && trim ? trimArt(art) : art), [art, trim])
	const name = trim ? `${entry.id}-trimmed` : entry.id
	const ink = toHexColor(LCD_INK)
	const vector = format === 'svg' || format === 'svg-lcd'
	const outW = out?.width ?? 48
	const outH = out?.height ?? 32

	const formats: { value: Format; label: string }[] = [
		{ value: 'png', label: 'PNG' },
		{ value: 'svg', label: 'SVG' },
		{ value: 'svg-lcd', label: 'SVG · LCD dots' },
		{ value: 'gif', label: 'GIF' }
	]
	const scales = SCALES.map(s => ({
		value: s,
		label: `${s}× (${outW * s}×${outH * s})`
	}))

	const download = async () => {
		if (!out) return
		if (format === 'png') save(await toPng(out, scale), `${name}@${scale}x.png`)
		else if (format === 'gif')
			save(await toGif(out, scale), `${name}@${scale}x.gif`)
		else if (format === 'svg')
			save(svgBlob(toSvg(out, { on: ink })), `${name}.svg`)
		else
			save(
				svgBlob(toSvg(out, { style: 'lcd', on: ink, off: `${ink}1f` })),
				`${name}-lcd.svg`
			)
	}
	const formatLabel = formats.find(f => f.value === format)?.label ?? ''
	const downloadLabel = vector
		? `Download ${formatLabel}`
		: `Download ${formatLabel} · ${outW * scale}×${outH * scale}`

	const copyC = async () => {
		if (!art) return
		await navigator.clipboard.writeText(toCArray(art, entry.title))
		setCopied(true)
		setTimeout(() => setCopied(false), 1500)
	}

	return (
		<div className="flex min-h-0 flex-1 flex-col">
			{/* Everything but the buttons scrolls; the buttons stay at the bottom. */}
			<div className="min-h-0 flex-1 overflow-y-auto">
				<DrawerHeader className="text-left">
					<DrawerTitle className="text-sm">
						{entry.title}{' '}
						<span className="text-muted-foreground">{entry.game}</span>
					</DrawerTitle>
					{(entry.publisher || entry.year) && (
						<DrawerDescription className="text-xs">
							{[entry.publisher, entry.year].filter(Boolean).join(' · ')}
						</DrawerDescription>
					)}
				</DrawerHeader>
				<div className="flex flex-col gap-4 p-4">
					<div className="flex aspect-[3/2] items-center justify-center">
						{preview ? (
							<div
								className="w-full"
								dangerouslySetInnerHTML={{ __html: preview }}
							/>
						) : (
							// The grid already loaded this thumbnail, so it shows instantly.
							<img
								src={`/thumbs/${entry.id}.png`}
								alt=""
								width={48}
								height={32}
								className="pixelated h-auto w-full dark:invert"
							/>
						)}
					</div>

					<div className="grid grid-cols-[auto_1fr] items-center gap-x-4 gap-y-3 text-sm">
						<span className="text-muted-foreground">Format</span>
						<Select
							items={formats}
							value={format}
							onValueChange={v => v && setFormat(v)}
						>
							<SelectTrigger aria-label="Format" className="w-full">
								<SelectValue />
							</SelectTrigger>
							<SelectContent alignItemWithTrigger={false}>
								{formats.map(f => (
									<SelectItem key={f.value} value={f.value}>
										{f.label}
									</SelectItem>
								))}
							</SelectContent>
						</Select>

						{/* Vectors have no pixel size, so scale only applies to PNG and GIF. */}
						{!vector && (
							<>
								<span className="text-muted-foreground">Scale</span>
								<Select
									items={scales}
									value={scale}
									onValueChange={v => v && setScale(v)}
								>
									<SelectTrigger aria-label="Scale" className="w-full">
										<SelectValue />
									</SelectTrigger>
									<SelectContent alignItemWithTrigger={false}>
										{scales.map(s => (
											<SelectItem key={s.value} value={s.value}>
												{s.label}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
							</>
						)}
					</div>
					<label className="flex items-center gap-3 text-sm">
						<Checkbox
							checked={trim}
							onCheckedChange={checked => setTrim(checked)}
						/>
						<span>Trim empty space</span>
					</label>
				</div>
			</div>
			<DrawerFooter className="pt-4">
				<button
					type="button"
					onClick={download}
					disabled={!out}
					className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 border px-4 py-2 text-left text-sm uppercase disabled:opacity-50"
				>
					{downloadLabel}
				</button>
				<button
					type="button"
					onClick={copyC}
					disabled={!art}
					className="border-border text-muted-foreground hover:text-foreground hover:border-foreground border px-4 py-2 text-left text-sm uppercase disabled:opacity-50"
				>
					{copied ? 'Copied!' : 'Copy as C array'}
				</button>
			</DrawerFooter>
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
