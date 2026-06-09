import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 border text-sm font-medium outline-none transition focus-visible:border-cyan/70 focus-visible:ring-2 focus-visible:ring-cyan/25 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "cinematic-button text-cyan hover:text-white",
        secondary: "cinematic-button-secondary text-slate-300 hover:text-ion",
        ghost: "border-transparent bg-transparent text-slate-400 hover:border-line/70 hover:bg-panel2/60 hover:text-white",
        destructive: "border-signal/45 bg-signal/10 text-signal shadow-signal hover:bg-signal/15",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        icon: "size-12 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export { buttonVariants };
