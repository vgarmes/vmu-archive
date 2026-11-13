'use client'

import { Input } from '@base-ui/react/input'
import { cn } from 'cn'
import { XIcon } from 'lucide-react'
import type { RefObject } from 'react'

/** The search field shared by the game list and a game's screens. */
export default function SearchBox({
	value,
	onChange,
	placeholder,
	label,
	inputRef
}: {
	value: string
	onChange: (value: string) => void
	placeholder: string
	label: string
	inputRef: RefObject<HTMLInputElement | null>
}) {
	return (
		<div
			role="search"
			className={cn(
				'border-border bg-card/50 focus-within:border-foreground focus-within:ring-foreground/30 box-border flex h-9 max-h-9 min-h-9 min-w-0 flex-1 items-center gap-2 border pl-3 transition-[border-color,box-shadow] focus-within:ring-1',
				// The clear button brings its own padding.
				value ? 'pr-1' : 'pr-3'
			)}
		>
			<svg
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				strokeWidth="2"
				strokeLinecap="round"
				strokeLinejoin="round"
				className="text-muted-foreground h-4 w-4 shrink-0"
				aria-hidden="true"
			>
				<path d="m21 21-4.34-4.34" />
				<circle cx="11" cy="11" r="8" />
			</svg>
			<Input
				type="text"
				enterKeyHint="search"
				value={value}
				onValueChange={onChange}
				placeholder={placeholder}
				aria-label={label}
				ref={inputRef}
				className="placeholder:text-muted-foreground h-full min-h-0 w-full min-w-0 flex-1 border-0 bg-transparent py-0 text-sm leading-5 ring-0 outline-none focus:outline-none"
			/>
			{value && (
				<button
					type="button"
					aria-label="Clear search"
					onClick={() => {
						onChange('')
						inputRef.current?.focus()
					}}
					className="text-muted-foreground hover:text-foreground focus-visible:ring-ring flex size-7 shrink-0 items-center justify-center outline-none focus-visible:ring-1"
				>
					<XIcon className="size-4" />
				</button>
			)}
		</div>
	)
}

/** The "nothing matches" state, with a way back to everything. */
export function NoMatches({
	message,
	onClear
}: {
	message: string
	onClear?: () => void
}) {
	return (
		<div className="flex flex-col items-center gap-4 py-16 text-center">
			<p className="text-muted-foreground">{message}</p>
			{onClear && (
				<button
					type="button"
					onClick={onClear}
					className="border-primary bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-primary focus-visible:ring-offset-background h-9 border px-4 text-xs uppercase transition-[background-color,box-shadow] outline-none focus-visible:ring-1 focus-visible:ring-offset-2"
				>
					Clear search
				</button>
			)}
		</div>
	)
}
