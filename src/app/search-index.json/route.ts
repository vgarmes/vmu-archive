import { getIcons, toIndexEntry } from '@/lib/icons'

export const dynamic = 'force-static'

/** The search index the grid fetches: every icon's metadata, no pixels. */
export function GET() {
	return Response.json(getIcons().map(toIndexEntry))
}
