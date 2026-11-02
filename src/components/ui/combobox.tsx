'use client'

import { Combobox as ComboboxPrimitive } from '@base-ui/react/combobox'
import { cn } from 'cn'
import { CheckIcon, ChevronDownIcon, XIcon } from 'lucide-react'

const Combobox = ComboboxPrimitive.Root

/**
 * The input, with a clear button (once something is picked) and a chevron
 * that opens the list. Styled like the archive's search box so the two sit
 * side by side.
 */
function ComboboxInput({ className, ...props }: ComboboxPrimitive.Input.Props) {
	return (
		<ComboboxPrimitive.InputGroup
			data-slot="combobox-input-group"
			className={cn(
				'border-border bg-card/50 focus-within:border-foreground focus-within:ring-foreground/30 box-border flex h-9 max-h-9 min-h-9 min-w-0 items-center gap-1 border pr-1 pl-3 transition-[border-color,box-shadow] focus-within:ring-1',
				className
			)}
		>
			<ComboboxPrimitive.Input
				data-slot="combobox-input"
				className="placeholder:text-muted-foreground h-full min-h-0 w-full min-w-0 flex-1 border-0 bg-transparent py-0 font-mono text-sm leading-5 ring-0 outline-none focus:outline-none"
				{...props}
			/>
			<ComboboxPrimitive.Clear
				data-slot="combobox-clear"
				aria-label="Clear"
				className="text-muted-foreground hover:text-foreground focus-visible:ring-ring flex size-7 shrink-0 items-center justify-center outline-none focus-visible:ring-1"
			>
				<XIcon className="size-4" />
			</ComboboxPrimitive.Clear>
			<ComboboxPrimitive.Trigger
				data-slot="combobox-trigger"
				aria-label="Show options"
				className="text-muted-foreground hover:text-foreground focus-visible:ring-ring flex size-7 shrink-0 items-center justify-center outline-none focus-visible:ring-1"
			>
				<ChevronDownIcon className="size-4" />
			</ComboboxPrimitive.Trigger>
		</ComboboxPrimitive.InputGroup>
	)
}

function ComboboxContent({
	className,
	children,
	sideOffset = 4,
	align = 'start',
	...props
}: ComboboxPrimitive.Popup.Props &
	Pick<ComboboxPrimitive.Positioner.Props, 'align' | 'sideOffset'>) {
	return (
		<ComboboxPrimitive.Portal>
			<ComboboxPrimitive.Positioner
				sideOffset={sideOffset}
				align={align}
				className="isolate z-50"
			>
				<ComboboxPrimitive.Popup
					data-slot="combobox-content"
					className={cn(
						'bg-popover text-popover-foreground ring-foreground/10 data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95 relative isolate z-50 max-h-[min(var(--available-height),20rem)] w-(--anchor-width) min-w-48 origin-(--transform-origin) overflow-x-hidden overflow-y-auto overscroll-contain p-1 shadow-md ring-1 duration-100',
						className
					)}
					{...props}
				>
					{children}
				</ComboboxPrimitive.Popup>
			</ComboboxPrimitive.Positioner>
		</ComboboxPrimitive.Portal>
	)
}

function ComboboxList({ className, ...props }: ComboboxPrimitive.List.Props) {
	return (
		<ComboboxPrimitive.List
			data-slot="combobox-list"
			className={cn('outline-none', className)}
			{...props}
		/>
	)
}

function ComboboxEmpty({ className, ...props }: ComboboxPrimitive.Empty.Props) {
	return (
		<ComboboxPrimitive.Empty
			data-slot="combobox-empty"
			className={cn(
				'text-muted-foreground px-2 py-1.5 text-sm empty:hidden',
				className
			)}
			{...props}
		/>
	)
}

function ComboboxItem({
	className,
	children,
	...props
}: ComboboxPrimitive.Item.Props) {
	return (
		<ComboboxPrimitive.Item
			data-slot="combobox-item"
			className={cn(
				'data-highlighted:bg-accent data-highlighted:text-accent-foreground relative flex w-full cursor-default items-center gap-2 py-1.5 pr-8 pl-2 text-sm outline-hidden select-none data-disabled:pointer-events-none data-disabled:opacity-50',
				className
			)}
			{...props}
		>
			{children}
			<ComboboxPrimitive.ItemIndicator
				render={
					<span className="pointer-events-none absolute right-2 flex size-4 items-center justify-center">
						<CheckIcon className="size-4" />
					</span>
				}
			/>
		</ComboboxPrimitive.Item>
	)
}

export {
	Combobox,
	ComboboxContent,
	ComboboxEmpty,
	ComboboxInput,
	ComboboxItem,
	ComboboxList
}
