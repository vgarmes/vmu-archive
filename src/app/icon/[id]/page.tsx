import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import IconDetail from '@/components/IconDetail'
import { getIcon, getIcons } from '@/lib/icons'

export const dynamicParams = false

export function generateStaticParams() {
	return getIcons().map(icon => ({ id: icon.id }))
}

export async function generateMetadata({
	params
}: PageProps<'/icon/[id]'>): Promise<Metadata> {
	const icon = getIcon((await params).id)
	if (!icon) return {}
	const { title, game } = icon.data
	return {
		title,
		description: `${title} (${game}): Dreamcast VMU pixel art, free to download.`
	}
}

export default async function IconPage({ params }: PageProps<'/icon/[id]'>) {
	const icon = getIcon((await params).id)
	if (!icon) notFound()
	const { data } = icon
	const art = {
		width: data.width,
		height: data.height,
		bpp: data.bpp,
		frames: data.frames,
		frameDelayMs: data.frameDelayMs
	}
	const facts: [string, string | number | undefined][] = [
		['Game', data.game],
		['Publisher', data.publisher],
		['Year', data.year],
		['Region', data.region],
		['Size', '48×32, 1-bit (VMU screen)'],
		['Frames', data.frames.length],
		['Source', data.source]
	]

	return (
		<>
			<Link
				href="/"
				className="text-muted-foreground hover:text-foreground text-sm"
			>
				← All icons
			</Link>
			<h1 className="mt-4 mb-6 text-2xl font-bold tracking-tight">
				{data.title}
			</h1>

			<IconDetail id={icon.id} title={data.title} art={art} />

			<dl className="border-border mt-10 grid grid-cols-[auto_1fr] gap-x-8 gap-y-2 border-t pt-6 text-sm">
				{facts
					.filter(([, value]) => value !== undefined && value !== '')
					.map(([label, value]) => (
						<div key={label} className="contents">
							<dt className="text-muted-foreground">{label}</dt>
							<dd>{value}</dd>
						</div>
					))}
				{data.tags.length > 0 && (
					<>
						<dt className="text-muted-foreground">Tags</dt>
						<dd className="flex flex-wrap gap-2">
							{data.tags.map(tag => (
								<Link
									key={tag}
									href={`/?q=${encodeURIComponent(tag)}`}
									className="border-border hover:border-foreground border px-2"
								>
									{tag}
								</Link>
							))}
						</dd>
					</>
				)}
			</dl>
		</>
	)
}
