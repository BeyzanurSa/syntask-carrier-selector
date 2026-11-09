"use client";

import { Toaster as Sonner, type ToasterProps } from "sonner";

/** App-wide toast host; colors follow the theme tokens. The app has a single light theme. */
export function Toaster(props: ToasterProps) {
  return (
    <Sonner
      theme="light"
      position="bottom-right"
      richColors
      closeButton
      duration={4000}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
}
