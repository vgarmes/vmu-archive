import { cn } from 'cn'
import type { SaveIconEntry } from '@/lib/save-icons'

/**
 * A save icon at a whole-number multiple of its 32x32, so its pixels stay
 * square: the width class must be one (w-16, w-24…). In its own colours, so
 * unlike the VMU art it isn't inverted in dark mode. Animated icons play their
 * GIF.
 */
export default function SaveIconImage({
	icon,
	className
}: {
	icon: Pick<SaveIconEntry, 'id' | 'title' | 'game' | 'frames'>
	className?: string
}) {
	return (
		<img
			src={`/save-icons/${icon.id}.${icon.frames > 1 ? 'gif' : 'png'}`}
			alt={`${icon.game}: ${icon.title}`}
			width={32}
			height={32}
			loading="lazy"
			className={cn('pixelated aspect-square h-auto', className)}
		/>
	)
}
