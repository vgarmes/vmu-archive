import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { z } from 'zod'

/** Site updates, hand-written in content/changelog.json and read at build time. */
const FILE = path.join(process.cwd(), 'content/changelog.json')

const schema = z.array(
	z.object({
		date: z.iso.date(),
		title: z.string().min(1),
		body: z.string().optional()
	})
)

export type ChangelogEntry = z.infer<typeof schema>[number]

/** Every entry, newest first. */
export function getChangelog(): ChangelogEntry[] {
	const parsed = schema.safeParse(JSON.parse(fs.readFileSync(FILE, 'utf8')))
	if (!parsed.success)
		throw new Error(`content/changelog.json: ${parsed.error.message}`)
	return parsed.data.sort((a, b) => b.date.localeCompare(a.date))
}
