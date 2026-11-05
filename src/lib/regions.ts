/**
 * The regions a screen, sprite or save icon can belong to, when it's only in
 * that region's release: Japan (NTSC-J), North America (NTSC-U) or Europe
 * (PAL). A piece in every release has no region. Run by Node directly from
 * the importers and checks: keep it free of imports and non-erasable
 * TypeScript.
 */
export const REGIONS = ['ntsc-j', 'ntsc-u', 'pal'] as const

export type Region = (typeof REGIONS)[number]

export const isRegion = (v: unknown): v is Region =>
	(REGIONS as readonly unknown[]).includes(v)
