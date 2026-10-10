'use client'

import { BracesIcon, CheckIcon } from 'lucide-react'
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
	DEFAULT_FRAME_DELAY_MS,
	encodeFrame,
	LCD_INK,
	parseColor,
	distinctFrames,
	toCArray,
	toHexColor,
	toRgba,
	toSheet,
	toSvg,
	toAnimatedSvg,
	toSvgSheet,
	trimArt,
	trimBox,
	withFrame,
	type PixelArt
} from '@/lib/pixels'

/**
 * The sprite drawer: a large preview and the export options. It slides in
 * from the right on desktop and up from the bottom, with a swipe handle, on
 * smaller screens.
 *
 * No extra data is fetched: the pixels are read back from the thumbnail the
 * grid already loaded (a native 48x32 PNG where opaque means lit, with
 * animation frames stacked below each other), and every export is generated
 * in the browser from them. Animations always play in the preview, unless the
 * visitor asks for reduced motion or picks a single frame to export. PNG and
 * SVG export an animation as a sprite sheet (frames side by side) or one frame;
 * GIF and the C array always hold every frame.
 */

const SCALES = [1, 4, 8, 16]
/** Above this width the drawer is a side panel rather than a bottom sheet. */
const DESKTOP = '(min-width: 768px)'

type Format = 'png' | 'svg' | 'svg-lcd' | 'gif'
/** Which frames of an animation to export: all as a sheet, or one (its index). */
type Frames = 'all' | number
/**
 * The Frames select's value: "all" (a sheet), "animated" (an SVG that plays
 * itself; SVG formats only) or a frame index, as a string.
 */
type FramesChoice = 'all' | 'animated' | `${number}`

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

function useReducedMotion() {
	const [reduced, setReduced] = useState(false)
	useEffect(() => {
		const media = matchMedia('(prefers-reduced-motion: reduce)')
		const update = () => setReduced(media.matches)
		update()
		media.addEventListener('change', update)
		return () => media.removeEventListener('change', update)
	}, [])
	return reduced
}

/** The sprite's pixels, read from its (already cached) thumbnail. */
function useThumbnailArt(entry: IndexEntry) {
	const { id, frameDelayMs } = entry
	const [read, setRead] = useState<{ id: string; art: PixelArt } | null>(null)
	useEffect(() => {
		const cached = artCache.get(id)
		if (cached) return setRead({ id, art: cached })
		let cancelled = false
		const img = new Image()
		img.onload = () => {
			// One 48x32 frame per 32 rows of the strip.
			const count = Math.max(1, Math.floor(img.naturalHeight / 32))
			const canvas = document.createElement('canvas')
			canvas.width = 48
			canvas.height = 32 * count
			const ctx = canvas.getContext('2d')!
			ctx.drawImage(img, 0, 0)
			const { data } = ctx.getImageData(0, 0, 48, 32 * count)
			const frames = Array.from({ length: count }, (_, f) =>
				encodeFrame(
					Array.from({ length: 48 * 32 }, (_, i) =>
						data[(f * 48 * 32 + i) * 4 + 3] >= 128 ? 1 : 0
					),
					1
				)
			)
			const art: PixelArt = { width: 48, height: 32, bpp: 1, frames }
			if (count > 1) art.frameDelayMs = frameDelayMs
			artCache.set(id, art)
			if (!cancelled) setRead({ id, art })
		}
		img.src = `/thumbs/${id}.png`
		return () => {
			cancelled = true
		}
	}, [id, frameDelayMs])
	return read && read.id === id ? read.art : null
}

/**
 * The frame to show now: cycles through an animation while `playing`, else
 * always 0.
 */
function useFrame(art: PixelArt | null, playing: boolean) {
	const reduced = useReducedMotion()
	const [frame, setFrame] = useState(0)
	const count = art?.frames.length ?? 1
	const delay = art?.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS
	useEffect(() => {
		setFrame(0)
		if (count < 2 || reduced || !playing) return
		const timer = setInterval(() => setFrame(f => (f + 1) % count), delay)
		return () => clearInterval(timer)
	}, [count, delay, reduced, playing])
	return Math.min(frame, count - 1)
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
	const art = useThumbnailArt(entry)
	const [scale, setScale] = useState<number>(8)
	const [copied, setCopied] = useState(false)
	const [trim, setTrim] = useState(false)
	const [format, setFormat] = useState<Format>('png')
	const [frames, setFrames] = useState<FramesChoice>('all')

	// The Frames row only applies to animations, and not to GIF, which is
	// always the whole animation.
	const animated = (art?.frames.length ?? 0) > 1
	const vector = format === 'svg' || format === 'svg-lcd'
	// "Animated" is only offered for SVG; for other formats it reads as "all".
	const choice: FramesChoice = frames === 'animated' && !vector ? 'all' : frames
	const selfPlaying = animated && choice === 'animated'
	const pick: Frames =
		animated && format !== 'gif' && choice !== 'all' && choice !== 'animated'
			? Number(choice)
			: 'all'
	const playing = useFrame(art, pick === 'all')
	const frame = pick === 'all' ? playing : pick
	const poses = useMemo(() => (art ? distinctFrames(art) : []), [art])
	const poseNumber = pick === 'all' ? 0 : poses.indexOf(pick) + 1
	const sheet = animated && pick === 'all' && format !== 'gif' && !selfPlaying
	const delay = art?.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS

	// With trim on, the unlit dots are drawn only inside the area the download
	// keeps: the shared box for an animation, a single frame's own box.
	const keptBox = useMemo(() => {
		if (!art || !trim) return undefined
		return trimBox(pick === 'all' ? art : withFrame(art, pick)) ?? undefined
	}, [art, trim, pick])

	const preview = art
		? toSvg(art, {
				frame,
				style: 'lcd',
				on: 'currentColor',
				off: 'color-mix(in srgb, currentColor 10%, transparent)',
				offBox: keptBox,
				attrs: 'class="block h-auto w-full" aria-hidden="true"'
			})
		: null

	// Downloads use the trimmed art when asked; the C array never does, since
	// VMU code expects the whole 48x32 screen.
	const out = useMemo(() => (art && trim ? trimArt(art) : art), [art, trim])
	// What a PNG holds: one frame, every frame side by side, or the still. A
	// single frame is trimmed to its own box; frames that play together share
	// one so they stay aligned.
	const still = useMemo(() => {
		if (!out || !animated || format === 'gif') return out
		if (pick === 'all') return toSheet(out)
		const one = withFrame(art!, pick)
		return trim ? trimArt(one) : one
	}, [out, art, animated, format, pick, trim])
	const name =
		(trim ? `${entry.id}-trimmed` : entry.id) +
		(selfPlaying
			? '-animated'
			: sheet
				? `-sheet-${out?.frames.length}f-${delay}ms`
				: animated && pick !== 'all'
					? `-frame-${poseNumber}`
					: '')
	const ink = toHexColor(LCD_INK)
	// Unlit LCD dots: the ink at ~12% opacity. toHexColor already includes the
	// alpha, so build the colour rather than appending to `ink`.
	const [r, g, b] = LCD_INK
	const unlit = toHexColor([r, g, b, 0x1f])
	// GIFs are frame-sized; everything else is the size of `still`.
	const sized = format === 'gif' ? out : still
	const outW = sized?.width ?? 48
	const outH = sized?.height ?? 32
	const frameOptions: { value: FramesChoice; label: string }[] = [
		{ value: 'all', label: 'All frames · sheet' },
		...(vector
			? [{ value: 'animated' as const, label: 'All frames · animated' }]
			: []),
		...poses.map(f => ({
			value: `${f}` as const,
			label: `Frame ${poses.indexOf(f) + 1}`
		}))
	]

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
		if (!out || !still) return
		// SVG sheets and animations keep each frame as its own group, so they're
		// drawn from the animation rather than from the merged sheet image.
		const svg = (opts: Parameters<typeof toSvg>[1]) =>
			selfPlaying
				? toAnimatedSvg(out, opts)
				: sheet
					? toSvgSheet(out, opts)
					: toSvg(still, opts)
		if (format === 'png')
			save(await toPng(still, scale), `${name}@${scale}x.png`)
		else if (format === 'gif')
			save(await toGif(out, scale), `${name}@${scale}x.gif`)
		else if (format === 'svg') save(svgBlob(svg({ on: ink })), `${name}.svg`)
		else
			save(
				svgBlob(svg({ style: 'lcd', on: ink, off: unlit })),
				`${name}-lcd.svg`
			)
	}
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
								// An animation's strip shows its first frame only.
								className="pixelated aspect-[3/2] h-auto w-full object-cover object-top dark:invert"
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

						{animated && format !== 'gif' && (
							<>
								<span className="text-muted-foreground">Frames</span>
								<Select
									items={frameOptions}
									value={choice}
									onValueChange={v => v && setFrames(v)}
								>
									<SelectTrigger aria-label="Frames" className="w-full">
										<SelectValue />
									</SelectTrigger>
									<SelectContent alignItemWithTrigger={false}>
										{frameOptions.map(f => (
											<SelectItem key={f.value} value={f.value}>
												{f.label}
											</SelectItem>
										))}
									</SelectContent>
								</Select>
							</>
						)}

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
				{/* The C array is a niche export, so it's an icon beside Download. */}
				<div className="flex gap-2">
					<button
						type="button"
						onClick={download}
						disabled={!out}
						className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 h-10 flex-1 border px-4 text-left text-sm uppercase disabled:opacity-50"
					>
						Download
					</button>
					<button
						type="button"
						onClick={copyC}
						disabled={!art}
						aria-label={copied ? 'Copied C array' : 'Copy as C array'}
						title={copied ? 'Copied!' : 'Copy as C array'}
						className="border-border text-muted-foreground hover:text-foreground hover:border-foreground flex size-10 shrink-0 items-center justify-center border disabled:opacity-50"
					>
						{copied ? (
							<CheckIcon className="size-4" aria-hidden="true" />
						) : (
							<BracesIcon className="size-4" aria-hidden="true" />
						)}
					</button>
				</div>
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
			delay: art.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS,
			transparent: transparentIndex >= 0,
			transparentIndex: Math.max(0, transparentIndex)
		})
	}
	gif.finish()
	return new Blob([gif.bytes() as Uint8Array<ArrayBuffer>], {
		type: 'image/gif'
	})
}
