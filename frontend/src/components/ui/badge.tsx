import { cva, type VariantProps } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center border px-2.5 py-1 text-xs font-medium uppercase tracking-normal shadow-electric", {
  variants: {
    variant: {
      default: "border-cyan/35 bg-cyan/10 text-cyan",
      success: "border-mint/35 bg-mint/10 text-mint",
      warning: "border-amber/40 bg-amber/10 text-amber",
      critical: "border-signal/45 bg-signal/10 text-signal",
      muted: "border-line/70 bg-panel2/70 text-slate-400",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
