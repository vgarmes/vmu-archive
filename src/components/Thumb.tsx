'use client'

import { cn } from 'cn'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { IndexEntry } from '@/lib/icons'
import { thumbPosition } from '@/lib/pixels'

/** Each animation's GIF, fetched the first time its card is hovered. */
const gifs = new Map<string, Promise<Blob>>()
function gifBlob(id: string) {
	let blob = gifs.get(id)
	if (!blob) {
		blob = fetch(`/thumbs/${id}.gif`).then(r =>
			r.ok ? r.blob() : Promise.reject(new Error(r.statusText))
		)
		blob.catch(() => gifs.delete(id))
		gifs.set(id, blob)
	}
	return blob
}

/**
 * Plays an animated card's GIF while it's hovered or keyboard-focused, and
 * shows its PNG still (the poster frame) otherwise. Each play gets a fresh
 * blob URL, so it starts from the first frame rather than wherever the GIF's
 * clock had got to, and the still stays up until the GIF has decoded.
 *
 * Spread `handlers` on the card's link.
 */
export function useHoverGif(icon: IndexEntry) {
	const [src, setSrc] = useState<string | null>(null)
	const play = useRef(0)
	const url = useRef<string | null>(null)

	const stop = useCallback(() => {
		play.current++
		if (url.current) URL.revokeObjectURL(url.current)
		url.current = null
		setSrc(null)
	}, [])

	const start = useCallback(async () => {
		if (!icon.frames || url.current) return
		if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
		const id = ++play.current
		const blob = await gifBlob(icon.id).catch(() => null)
		if (!blob || id !== play.current) return
		const next = URL.createObjectURL(blob)
		// Load it before swapping, so the still stays up until the GIF can show.
		// (`decode()` sometimes never settled for these in Chrome.)
		await new Promise(resolve => {
			const img = new Image()
			img.onload = img.onerror = resolve
			img.src = next
		})
		if (id !== play.current) return URL.revokeObjectURL(next)
		url.current = next
		setSrc(next)
	}, [icon])

	useEffect(() => stop, [stop])
	return {
		src,
		handlers: {
			onPointerEnter: (e: React.PointerEvent) =>
				e.pointerType === 'mouse' && start(),
			onPointerLeave: stop,
			onFocus: (e: React.FocusEvent) =>
				e.currentTarget.matches(':focus-visible') && start(),
			onBlur: stop
		}
	}
}

/** A card's 3:2 picture: the icon's still, or `gifSrc` while it plays. */
export function Thumb({
	icon,
	gifSrc
}: {
	icon: IndexEntry
	gifSrc: string | null
}) {
	return (
		/*
			The image is absolutely positioned so it can't stretch the 3:2 box;
			a percentage height on an in-flow image let Safari grow the box.
		*/
		<div className="relative aspect-[3/2]">
			<img
				src={gifSrc ?? `/thumbs/${icon.id}.png`}
				alt=""
				width={48}
				height={32}
				loading="lazy"
				decoding="async"
				// The art is near-black; flip it for dark mode. An animation's
				// PNG is a strip of its frames, cropped to the poster frame; its
				// GIF (on hover) is one frame tall, so the crop shows all of it.
				className={cn(
					'pixelated absolute inset-0 m-auto size-4/5 dark:invert',
					icon.frames ? 'object-cover object-top' : 'object-contain'
				)}
				style={
					thumbPosition(icon) && !gifSrc
						? { objectPosition: thumbPosition(icon) }
						: undefined
				}
			/>
		</div>
	)
}
