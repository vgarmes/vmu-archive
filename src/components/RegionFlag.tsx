import { cn } from 'cn'
import type { IndexEntry } from '@/lib/icons'

/** Flags we have art for, from flag-icons (MIT, 4:3). Other regions show nothing. */
const FLAGS: Partial<
	Record<NonNullable<IndexEntry['region']>, { src: string; label: string }>
> = {
	'ntsc-j': { src: '/flags/jp.svg', label: 'Japan (NTSC-J)' }
}

/** A small flag for a screen that belongs to one region's release. */
export default function RegionFlag({
	region,
	className
}: {
	region: IndexEntry['region']
	className?: string
}) {
	const flag = region && FLAGS[region]
	if (!flag) return null
	return (
		<img
			src={flag.src}
			alt={flag.label}
			title={flag.label}
			width={12}
			height={9}
			// The outline keeps the white field visible on a light background.
			className={cn(
				'outline-border inline-block h-[9px] w-3 shrink-0 outline',
				className
			)}
		/>
	)
}
