/**
 * A URL-safe slug ("Tony Hawk's Pro Skater" → "tony-hawks-pro-skater"), used
 * for icon ids by the importer and for ?game= in the archive's URL.
 *
 * Run by Node directly from the importer, like pixels.ts: keep it free of
 * imports and non-erasable TypeScript.
 */
export const slug = (s: string) =>
	s
		.normalize('NFKD')
		// Drop the accents NFKD splits off, so "Rōko" → roko, not ro-ko.
		.replace(/[̀-ͯ]/g, '')
		.toLowerCase()
		// "Tony Hawk's" → tony-hawks, not tony-hawk-s.
		.replace(/['’]/g, '')
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '') || 'icon'
