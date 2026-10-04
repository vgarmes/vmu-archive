declare module 'gifenc' {
	type Palette = number[][]
	interface Encoder {
		writeFrame(
			index: Uint8Array,
			width: number,
			height: number,
			opts?: {
				palette?: Palette
				delay?: number
				transparent?: boolean
				transparentIndex?: number
				repeat?: number
			}
		): void
		finish(): void
		bytes(): Uint8Array
	}
	export function GIFEncoder(): Encoder
}
