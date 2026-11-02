/**
 * A small GIF decoder for the importer: every frame composited onto the full
 * canvas (as a browser shows it), as RGBA, with its delay in milliseconds.
 * Transparent pixels come out with alpha 0.
 */

export interface GifFrame {
	width: number
	height: number
	data: Uint8Array
	delayMs: number
}

/** Browsers show a frame with no (or a 10 ms) delay for 100 ms. */
const MIN_DELAY_CS = 2
const DEFAULT_DELAY_MS = 100

export function decodeGif(buf: Uint8Array): GifFrame[] {
	const sig = String.fromCharCode(...buf.subarray(0, 6))
	if (sig !== 'GIF87a' && sig !== 'GIF89a') throw new Error('not a GIF file')
	const u16 = (p: number) => buf[p] | (buf[p + 1] << 8)

	const width = u16(6)
	const height = u16(8)
	let p = 13
	let globalTable: Uint8Array | null = null
	if (buf[10] & 0x80) {
		const size = 3 * (1 << ((buf[10] & 7) + 1))
		globalTable = buf.subarray(p, p + size)
		p += size
	}

	/** The data sub-blocks starting at `p`, joined; moves `p` past them. */
	const subBlocks = () => {
		const parts: Uint8Array[] = []
		let len = 0
		while (p < buf.length && buf[p] !== 0) {
			parts.push(buf.subarray(p + 1, p + 1 + buf[p]))
			len += buf[p]
			p += buf[p] + 1
		}
		p++
		const out = new Uint8Array(len)
		let at = 0
		for (const part of parts) {
			out.set(part, at)
			at += part.length
		}
		return out
	}

	const canvas = new Uint8Array(width * height * 4)
	const frames: GifFrame[] = []
	let delayCs = 0
	let disposal = 0
	let transparent = -1

	while (p < buf.length) {
		const block = buf[p++]
		if (block === 0x3b) break
		if (block === 0x21) {
			const label = buf[p++]
			if (label === 0xf9) {
				const packed = buf[p + 1]
				disposal = (packed >> 2) & 7
				delayCs = u16(p + 2)
				transparent = packed & 1 ? buf[p + 4] : -1
			}
			subBlocks()
			continue
		}
		if (block !== 0x2c)
			throw new Error(`unexpected GIF block 0x${block.toString(16)}`)

		const left = u16(p)
		const top = u16(p + 2)
		const w = u16(p + 4)
		const h = u16(p + 6)
		const packed = buf[p + 8]
		p += 9
		let table = globalTable
		if (packed & 0x80) {
			const size = 3 * (1 << ((packed & 7) + 1))
			table = buf.subarray(p, p + size)
			p += size
		}
		if (!table) throw new Error('GIF frame has no colour table')
		const minCodeSize = buf[p++]
		let indices = lzw(minCodeSize, subBlocks(), w * h)
		if (packed & 0x40) indices = deinterlace(indices, w, h)

		const saved = disposal === 3 ? canvas.slice() : null
		for (let y = 0; y < h; y++)
			for (let x = 0; x < w; x++) {
				const cx = left + x
				const cy = top + y
				if (cx >= width || cy >= height) continue
				const index = indices[y * w + x]
				if (index === transparent) continue
				const o = (cy * width + cx) * 4
				canvas[o] = table[index * 3]
				canvas[o + 1] = table[index * 3 + 1]
				canvas[o + 2] = table[index * 3 + 2]
				canvas[o + 3] = 255
			}
		frames.push({
			width,
			height,
			data: canvas.slice(),
			delayMs: delayCs < MIN_DELAY_CS ? DEFAULT_DELAY_MS : delayCs * 10
		})

		// What the next frame is drawn over.
		if (disposal === 2)
			for (let y = top; y < Math.min(top + h, height); y++)
				canvas.fill(
					0,
					(y * width + left) * 4,
					(y * width + Math.min(left + w, width)) * 4
				)
		else if (saved) canvas.set(saved)
		delayCs = 0
		disposal = 0
		transparent = -1
	}
	if (!frames.length) throw new Error('GIF has no frames')
	return frames
}

/** GIF's variable-width LZW: `count` colour indices. */
function lzw(minCodeSize: number, data: Uint8Array, count: number) {
	const clear = 1 << minCodeSize
	const end = clear + 1
	const prefix = new Int16Array(4096)
	const suffix = new Uint8Array(4096)
	for (let i = 0; i < clear; i++) suffix[i] = i
	const stack = new Uint8Array(4097)
	const out = new Uint8Array(count)

	let size = minCodeSize + 1
	let next = end + 1
	let old = -1
	let first = 0
	let acc = 0
	let bits = 0
	let pos = 0
	let op = 0
	while (op < count) {
		while (bits < size) {
			if (pos >= data.length) return out
			acc |= data[pos++] << bits
			bits += 8
		}
		const code = acc & ((1 << size) - 1)
		acc >>= size
		bits -= size

		if (code === clear) {
			size = minCodeSize + 1
			next = end + 1
			old = -1
			continue
		}
		if (code === end) break
		if (old === -1) {
			out[op++] = suffix[code]
			old = first = code
			continue
		}
		let c = code
		let sp = 0
		// A code not in the table yet is the previous string plus its own first byte.
		if (code >= next) {
			stack[sp++] = first
			c = old
		}
		while (c >= clear) {
			stack[sp++] = suffix[c]
			c = prefix[c]
		}
		first = c
		stack[sp++] = c
		if (next < 4096) {
			prefix[next] = old
			suffix[next] = first
			next++
			if (next === 1 << size && size < 12) size++
		}
		while (sp && op < count) out[op++] = stack[--sp]
		old = code
	}
	return out
}

/** Interlaced rows come in four passes; put them back in order. */
function deinterlace(indices: Uint8Array, w: number, h: number) {
	const out = new Uint8Array(indices.length)
	let row = 0
	for (const [start, step] of [
		[0, 8],
		[4, 8],
		[2, 4],
		[1, 2]
	])
		for (let y = start; y < h; y += step)
			out.set(indices.subarray(row * w, ++row * w), y * w)
	return out
}
