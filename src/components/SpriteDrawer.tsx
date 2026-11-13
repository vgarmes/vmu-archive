'use client'

import { ArrowLeftRightIcon } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import RegionFlag from '@/components/RegionFlag'
import { Badge } from '@/components/ui/badge'
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
	frameDelays,
	gifFrames,
	LCD_INK,
	parseColor,
	scrollFrames,
	STRIP_GAP,
	thumbPosition,
	distinctFrames,
	toHexColor,
	toRgba,
	toSheet,
	toSvg,
	toAnimatedSvg,
	toSvgSheet,
	trimArt,
	trimBox,
	withFrame,
	type PixelArt,
	type Rgba
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
 * GIF always holds every frame. A scroll's thumbnail is its strip, which is what
 * PNG and SVG export (or, in SVG, the scroll playing); it has no single frames.
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

/**
 * Colour presets: the ink of lit pixels, used by every export, and the screen
 * behind them, used by the preview and the LCD-dots SVG only (the other
 * formats stay transparent). Those two draw unlit dots too, in `off`, with the
 * screen showing in the gaps between dots; without an `off` they're the ink
 * at ~12%. "Site theme" has none: the preview follows the page and exports use
 * the default ink, as before presets.
 */
const PALETTES = [
	{ id: 'site', name: 'Site theme', ink: null, off: null, screen: null },
	// VMU and LCD are the DreamPotato emulator's Dark Green and VM2 palettes,
	// all three tones: Screen1 (lit) as ink, Screen0 (unlit) as off and its
	// lighter Margin, the frame round the screen, as the screen in the gaps.
	{
		id: 'vmu',
		name: 'VMU',
		ink: '#231024',
		off: '#3e4e44',
		screen: '#4d594b'
	},
	{
		id: 'lcd',
		name: 'LCD',
		ink: '#000000',
		off: '#9fcede',
		screen: '#b5d3dd'
	},
	{ id: 'mono', name: 'Mono', ink: '#000000', off: null, screen: '#ffffff' },
	{
		id: 'gameboy',
		name: 'Game Boy',
		ink: '#0f380f',
		off: null,
		screen: '#9bbc0f'
	}
] as const
type PaletteId = (typeof PALETTES)[number]['id']
const COLORS_KEY = 'vmu-archive:colors'

/** The chosen preset and whether its colours are swapped, kept per browser. */
function useColors() {
	const [colors, setColors] = useState<{ id: PaletteId; swapped: boolean }>({
		id: 'site',
		swapped: false
	})
	useEffect(() => {
		try {
			const saved = JSON.parse(localStorage.getItem(COLORS_KEY) ?? 'null')
			if (saved && PALETTES.some(p => p.id === saved.id))
				setColors({ id: saved.id, swapped: !!saved.swapped })
		} catch {}
	}, [])
	const update = (next: { id: PaletteId; swapped: boolean }) => {
		setColors(next)
		try {
			localStorage.setItem(COLORS_KEY, JSON.stringify(next))
		} catch {}
	}
	const palette = PALETTES.find(p => p.id === colors.id) ?? PALETTES[0]
	const ink = colors.swapped ? palette.screen : palette.ink
	const screen = colors.swapped ? palette.ink : palette.screen
	// The middle tone stays put when ink and screen swap.
	return { ...colors, palette, ink, off: palette.off, screen, update }
}

/** A preset's colours: an ink square on its unlit colour, or its screen. */
function Swatch({
	ink,
	screen
}: {
	ink: string | null
	screen: string | null
}) {
	return (
		<span
			aria-hidden="true"
			className="border-border inline-flex size-4 shrink-0 border"
			style={{ background: screen ?? 'transparent' }}
		>
			<span
				className="m-auto size-2"
				style={{ background: ink ?? 'currentColor' }}
			/>
		</span>
	)
}

/** Sprites already read from their thumbnails this visit, by icon id. */
/** A sprite's frames, and for a scroll the strip they're cut from. */
interface Loaded {
	art: PixelArt
	strip?: PixelArt
}
const artCache = new Map<string, Loaded>()

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

/**
 * The sprite's pixels, read from its (already cached) thumbnail. A scroll's
 * thumbnail is its strip: the frames are cut from it here, as on the server.
 */
function useThumbnailArt(entry: IndexEntry): Loaded | null {
	const { id, frameDelayMs, frameDelaysMs } = entry
	const stripWidth = entry.scroll?.width
	const stripHeight = entry.scroll?.height ?? 32
	const stepPx = entry.scroll?.stepPx
	const direction = entry.scroll?.direction
	const [read, setRead] = useState<({ id: string } & Loaded) | null>(null)
	useEffect(() => {
		const cached = artCache.get(id)
		if (cached) return setRead({ id, ...cached })
		let cancelled = false
		const img = new Image()
		img.onload = () => {
			if (stripWidth && stepPx) {
				const canvas = document.createElement('canvas')
				canvas.width = stripWidth
				canvas.height = stripHeight
				const ctx = canvas.getContext('2d')!
				ctx.drawImage(img, 0, 0)
				const { data } = ctx.getImageData(0, 0, stripWidth, stripHeight)
				const hex = encodeFrame(
					Array.from({ length: stripWidth * stripHeight }, (_, i) =>
						data[i * 4 + 3] >= 128 ? 1 : 0
					),
					1
				)
				const delayMs = frameDelayMs ?? DEFAULT_FRAME_DELAY_MS
				const loaded: Loaded = {
					art: {
						width: 48,
						height: 32,
						bpp: 1,
						frames: scrollFrames(
							{
								width: stripWidth,
								height: stripHeight,
								strip: hex,
								stepPx,
								delayMs,
								direction
							},
							48,
							32,
							1
						),
						frameDelayMs: delayMs
					},
					strip: {
						width: stripWidth,
						height: stripHeight,
						bpp: 1,
						frames: [hex]
					}
				}
				artCache.set(id, loaded)
				if (!cancelled) setRead({ id, ...loaded })
				return
			}
			// One 48x32 frame every 32 + STRIP_GAP rows of the strip.
			const pitch = 32 + STRIP_GAP
			const count = Math.max(
				1,
				Math.floor((img.naturalHeight + STRIP_GAP) / pitch)
			)
			const canvas = document.createElement('canvas')
			canvas.width = 48
			canvas.height = img.naturalHeight
			const ctx = canvas.getContext('2d')!
			ctx.drawImage(img, 0, 0)
			const { data } = ctx.getImageData(0, 0, 48, img.naturalHeight)
			const frames = Array.from({ length: count }, (_, f) =>
				encodeFrame(
					Array.from({ length: 48 * 32 }, (_, i) =>
						data[(f * pitch * 48 + i) * 4 + 3] >= 128 ? 1 : 0
					),
					1
				)
			)
			const art: PixelArt = { width: 48, height: 32, bpp: 1, frames }
			if (count > 1) {
				art.frameDelayMs = frameDelayMs
				art.frameDelaysMs = frameDelaysMs
			}
			artCache.set(id, { art })
			if (!cancelled) setRead({ id, art })
		}
		img.src = `/thumbs/${id}.png`
		return () => {
			cancelled = true
		}
	}, [
		id,
		frameDelayMs,
		frameDelaysMs,
		stripWidth,
		stripHeight,
		stepPx,
		direction
	])
	return read && read.id === id ? read : null
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
	const loaded = useThumbnailArt(entry)
	const art = loaded?.art ?? null
	// A scroll exports as the strip it's cut from, not as its many frames.
	const strip = loaded?.strip
	const [scale, setScale] = useState<number>(8)
	const [trim, setTrim] = useState(false)
	const [format, setFormat] = useState<Format>('png')
	const [frames, setFrames] = useState<FramesChoice>('all')
	const colors = useColors()
	// Ink for every export: the preset's, or the default. Unlit LCD dots are
	// the preset's own unlit colour, or else the ink at ~12% opacity;
	// toHexColor already includes the alpha, so that colour is built rather
	// than appended to.
	const inkRgba = colors.ink ? parseColor(colors.ink) : LCD_INK
	const ink = toHexColor(inkRgba)
	const [r, g, b] = inkRgba
	const unlit = colors.off ?? toHexColor([r, g, b, 0x1f])

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
	const poses = useMemo(() => (art ? distinctFrames(art) : []), [art])
	const poseNumber = pick === 'all' ? 0 : poses.indexOf(pick) + 1
	const sheet = animated && pick === 'all' && format !== 'gif' && !selfPlaying
	// A sheet's name carries its timing: one delay, or each frame's.
	const delay = art?.frameDelaysMs
		? art.frameDelaysMs.join('-')
		: (art?.frameDelayMs ?? DEFAULT_FRAME_DELAY_MS)

	// With trim on, the unlit dots are drawn only inside the area the download
	// keeps: the shared box for an animation, a single frame's own box.
	const keptBox = useMemo(() => {
		if (!art || !trim) return undefined
		return trimBox(pick === 'all' ? art : withFrame(art, pick)) ?? undefined
	}, [art, trim, pick])

	// "Site theme" follows the page's text colour; a preset shows its own ink
	// on its screen colour, as the LCD-dots export will.
	const previewOpts = {
		style: 'lcd',
		...(colors.ink
			? { on: ink, off: unlit, background: colors.screen ?? undefined }
			: {
					on: 'currentColor',
					off: 'color-mix(in srgb, currentColor 10%, transparent)'
				}),
		offBox: keptBox,
		// Decorative, so touches land on its (stable) wrapper instead.
		attrs: 'class="pointer-events-none block h-auto w-full" aria-hidden="true"'
	} as const
	// An animation plays as the self-playing SVG, so the preview's markup is
	// set once rather than replaced every frame. Safari keeps sending a touch to
	// the element it started on; when that element was replaced mid-swipe, the
	// drawer never saw the release and stayed part-way down. Its CSS also holds
	// frame 1 for reduced motion.
	const preview = art
		? animated && pick === 'all'
			? toAnimatedSvg(art, previewOpts)
			: toSvg(art, { ...previewOpts, frame: pick === 'all' ? 0 : pick })
		: null

	// Downloads use the trimmed art when asked.
	const out = useMemo(() => (art && trim ? trimArt(art) : art), [art, trim])
	// What a PNG holds: one frame, every frame side by side, or the still. A
	// single frame is trimmed to its own box; frames that play together share
	// one so they stay aligned.
	const still = useMemo(() => {
		if (!out || !animated || format === 'gif') return out
		if (pick === 'all')
			return strip ? (trim ? trimArt(strip) : strip) : toSheet(out)
		const one = withFrame(art!, pick)
		return trim ? trimArt(one) : one
	}, [out, art, strip, animated, format, pick, trim])
	const name =
		(trim ? `${entry.id}-trimmed` : entry.id) +
		(selfPlaying
			? '-animated'
			: sheet
				? strip
					? '-strip'
					: `-sheet-${out?.frames.length}f-${delay}ms`
				: animated && pick !== 'all'
					? `-frame-${poseNumber}`
					: '')
	// GIFs are frame-sized; everything else is the size of `still`.
	const sized = format === 'gif' ? out : still
	const outW = sized?.width ?? 48
	const outH = sized?.height ?? 32
	// A scroll offers its strip and the animation, not hundreds of 1-pixel steps.
	const frameOptions: { value: FramesChoice; label: string }[] = [
		{ value: 'all', label: strip ? 'Whole strip' : 'All frames · sheet' },
		...(vector
			? [{ value: 'animated' as const, label: 'All frames · animated' }]
			: []),
		...(strip
			? []
			: poses.map(f => ({
					value: `${f}` as const,
					label: `Frame ${poses.indexOf(f) + 1}`
				})))
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
				: sheet && !strip
					? toSvgSheet(out, opts)
					: toSvg(still, opts)
		if (format === 'png')
			save(await toPng(still, scale, inkRgba), `${name}@${scale}x.png`)
		else if (format === 'gif')
			save(
				await toGif(gifFrames(out, !!strip), scale, inkRgba),
				`${name}@${scale}x.gif`
			)
		else if (format === 'svg') save(svgBlob(svg({ on: ink })), `${name}.svg`)
		else
			save(
				svgBlob(
					svg({
						style: 'lcd',
						on: ink,
						off: unlit,
						background: colors.screen ?? undefined
					})
				),
				`${name}-lcd.svg`
			)
	}

	return (
		<div className="flex min-h-0 flex-1 flex-col">
			{/* Everything but the buttons scrolls; the buttons stay at the bottom. */}
			<div className="min-h-0 flex-1 overflow-y-auto">
				<DrawerHeader className="text-left">
					<DrawerTitle className="text-sm">
						{entry.title}{' '}
						<span className="text-muted-foreground">{entry.game}</span>
						<RegionFlag
							region={entry.region}
							className="ml-1.5 align-baseline"
						/>
					</DrawerTitle>
					{(entry.publisher || entry.year) && (
						<DrawerDescription className="text-xs">
							{[entry.publisher, entry.year].filter(Boolean).join(' · ')}
						</DrawerDescription>
					)}
					{entry.unused && (
						<Badge
							variant="outline"
							title="The game's code never shows this screen"
						>
							Unused
						</Badge>
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
								// An animation's strip shows one frame: its poster, as in the grid.
								className="pixelated aspect-[3/2] h-auto w-full object-cover object-top dark:invert"
								style={
									thumbPosition(entry)
										? { objectPosition: thumbPosition(entry) }
										: undefined
								}
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

						<span className="text-muted-foreground">Colors</span>
						<div className="flex min-w-0 gap-2">
							<Select
								items={PALETTES.map(p => ({ value: p.id, label: p.name }))}
								value={colors.id}
								onValueChange={v =>
									v && colors.update({ id: v, swapped: false })
								}
							>
								<SelectTrigger aria-label="Colors" className="min-w-0 flex-1">
									<SelectValue>
										{() => (
											<span className="flex items-center gap-2">
												<Swatch
													ink={colors.ink}
													screen={colors.off ?? colors.screen}
												/>
												{colors.palette.name}
											</span>
										)}
									</SelectValue>
								</SelectTrigger>
								<SelectContent alignItemWithTrigger={false}>
									{PALETTES.map(p => (
										<SelectItem key={p.id} value={p.id}>
											<span className="flex items-center gap-2">
												<Swatch ink={p.ink} screen={p.off ?? p.screen} />
												{p.name}
											</span>
										</SelectItem>
									))}
								</SelectContent>
							</Select>
							<button
								type="button"
								onClick={() =>
									colors.update({ id: colors.id, swapped: !colors.swapped })
								}
								disabled={!colors.palette.ink}
								aria-pressed={colors.swapped}
								aria-label="Swap ink and screen colors"
								title="Swap ink and screen colors"
								className="border-input hover:border-foreground text-muted-foreground hover:text-foreground aria-pressed:text-foreground flex size-8 shrink-0 items-center justify-center rounded-lg border disabled:opacity-40"
							>
								<ArrowLeftRightIcon className="size-4" aria-hidden="true" />
							</button>
						</div>

						{animated && format !== 'gif' && frameOptions.length > 1 && (
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
									<SelectTrigger
										aria-label="Scale"
										className="w-full font-mono"
									>
										<SelectValue />
									</SelectTrigger>
									<SelectContent alignItemWithTrigger={false}>
										{scales.map(s => (
											<SelectItem
												key={s.value}
												value={s.value}
												className="font-mono"
											>
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
					className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 h-10 w-full border px-4 text-center text-sm uppercase disabled:opacity-50"
				>
					Download
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

function toPng(art: PixelArt, scale: number, ink: Rgba): Promise<Blob> {
	const canvas = document.createElement('canvas')
	canvas.width = art.width * scale
	canvas.height = art.height * scale
	const data = new ImageData(
		toRgba(art, 0, scale, ink) as Uint8ClampedArray<ArrayBuffer>,
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
async function toGif(art: PixelArt, scale: number, ink: Rgba): Promise<Blob> {
	const { GIFEncoder } = await import('gifenc')
	const { width: w, height: h, bpp } = art
	const colors = bpp === 1 ? [[0, 0, 0, 0], ink] : art.palette!.map(parseColor)
	const palette = colors.map(([r, g, b]) => [r, g, b])
	const transparentIndex = colors.findIndex(c => c[3] === 0)
	const W = w * scale
	const H = h * scale

	const delays = frameDelays(art)
	const gif = GIFEncoder()
	art.frames.forEach((hex, f) => {
		const px = decodeFrame(hex, w, h, bpp)
		const big = new Uint8Array(W * H)
		for (let y = 0; y < H; y++)
			for (let x = 0; x < W; x++)
				big[y * W + x] = px[Math.floor(y / scale) * w + Math.floor(x / scale)]
		gif.writeFrame(big, W, H, {
			palette,
			delay: delays[f],
			transparent: transparentIndex >= 0,
			transparentIndex: Math.max(0, transparentIndex)
		})
	})
	gif.finish()
	return new Blob([gif.bytes() as Uint8Array<ArrayBuffer>], {
		type: 'image/gif'
	})
}
