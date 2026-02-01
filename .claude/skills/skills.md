# UI Design System - AI Learning Platform

This document provides comprehensive UI patterns and design tokens for the AI Learning Platform. Use these patterns to ensure visual consistency across all components.

---

## Design Tokens

### Colors (HSL Format)

All colors use HSL format for Tailwind CSS variables. Define in `globals.css`:

```css
:root {
  /* Base */
  --background: 0 0% 100%;           /* White */
  --foreground: 240 10% 3.9%;        /* Near black */

  /* Card/Popover */
  --card: 0 0% 100%;
  --card-foreground: 240 10% 3.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 240 10% 3.9%;

  /* Primary */
  --primary: 240 5.9% 10%;           /* Dark blue-gray */
  --primary-foreground: 0 0% 98%;    /* Off-white */

  /* Secondary */
  --secondary: 240 4.8% 95.9%;       /* Light gray */
  --secondary-foreground: 240 5.9% 10%;

  /* Muted */
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;

  /* Accent */
  --accent: 240 4.8% 95.9%;
  --accent-foreground: 240 5.9% 10%;

  /* Destructive */
  --destructive: 0 84.2% 60.2%;      /* Red */
  --destructive-foreground: 0 0% 98%;

  /* UI Elements */
  --border: 240 5.9% 90%;
  --input: 240 5.9% 90%;
  --ring: 240 5.9% 10%;
  --radius: 0.625rem;                /* 10px base radius */
}
```

### Semantic Color Usage

| Purpose | Light Mode | Tailwind Class |
|---------|------------|----------------|
| Background | White | `bg-background` or `bg-white` |
| Text Primary | Near black | `text-foreground` or `text-gray-900` |
| Text Secondary | Gray | `text-muted-foreground` or `text-gray-600` |
| Text Muted | Light gray | `text-gray-400` |
| Accent/Interactive | Blue | `bg-blue-500`, `text-blue-500` |
| Success | Green | `bg-green-500`, `text-green-600` |
| Error | Red | `bg-destructive`, `text-red-600` |
| Border | Light gray | `border-border` or `border-gray-200` |

---

## Typography

### Font Stack

Use system fonts for performance:

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Text Sizes

| Element | Size | Tailwind Class |
|---------|------|----------------|
| Body | 14-16px | `text-sm` or `text-base` |
| Small | 12px | `text-xs` |
| Heading 1 | 48-60px | `text-5xl` or `text-6xl` |
| Heading 2 | 36px | `text-4xl` |
| Heading 3 | 24px | `text-2xl` |
| Label | 14px | `text-sm font-medium` |

### Font Weights

- Regular: `font-normal` (400)
- Medium: `font-medium` (500)
- Semibold: `font-semibold` (600)
- Bold: `font-bold` (700)

---

## Border Radius

| Size | Value | Tailwind Class | Usage |
|------|-------|----------------|-------|
| XS | 4px | `rounded` | Small buttons |
| SM | 6px | `rounded-md` | Inputs, small elements |
| MD | 8px | `rounded-lg` | Buttons, badges |
| LG | 12px | `rounded-xl` | Cards, containers |
| XL | 16px | `rounded-2xl` | Large cards, chat bubbles |
| Full | 9999px | `rounded-full` | Circular elements, pills |

---

## Shadows

```css
/* Use Tailwind shadow classes */
shadow-xs    /* Subtle, inputs */
shadow-sm    /* Cards, buttons */
shadow-md    /* Elevated elements */
shadow-lg    /* Modals, dropdowns */
shadow-xl    /* Overlays */
```

---

## Spacing Scale

Use Tailwind's default spacing (4px base unit):

| Name | Value | Tailwind |
|------|-------|----------|
| 1 | 4px | `p-1`, `m-1`, `gap-1` |
| 2 | 8px | `p-2`, `m-2`, `gap-2` |
| 3 | 12px | `p-3`, `m-3`, `gap-3` |
| 4 | 16px | `p-4`, `m-4`, `gap-4` |
| 6 | 24px | `p-6`, `m-6`, `gap-6` |
| 8 | 32px | `p-8`, `m-8`, `gap-8` |

---

## Utility Function

Always use the `cn` utility for class merging:

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

## Component Patterns

### Button

```tsx
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-white hover:bg-destructive/90",
        outline: "border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md gap-1.5 px-3",
        lg: "h-10 rounded-md px-6",
        icon: "size-9",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

interface ButtonProps extends React.ComponentProps<"button">, VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button"
  return <Comp className={cn(buttonVariants({ variant, size, className }))} {...props} />
}

export { Button, buttonVariants }
```

### Card

```tsx
import { cn } from "@/lib/utils"

function Card({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        className
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("grid auto-rows-min gap-2 px-6", className)}
      {...props}
    />
  )
}

function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("leading-none font-semibold", className)} {...props} />
}

function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("text-muted-foreground text-sm", className)} {...props} />
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("px-6", className)} {...props} />
}

function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex items-center px-6", className)} {...props} />
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }
```

### Input

```tsx
import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "placeholder:text-muted-foreground border-input h-9 w-full min-w-0 rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none disabled:pointer-events-none disabled:opacity-50 md:text-sm",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        className
      )}
      {...props}
    />
  )
}

export { Input }
```

### Badge

```tsx
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-full border px-2 py-0.5 text-xs font-medium w-fit whitespace-nowrap shrink-0 gap-1 transition-[color,box-shadow] overflow-hidden",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-white",
        outline: "text-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

interface BadgeProps extends React.ComponentProps<"span">, VariantProps<typeof badgeVariants> {
  asChild?: boolean
}

function Badge({ className, variant, asChild = false, ...props }: BadgeProps) {
  const Comp = asChild ? Slot : "span"
  return <Comp className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
```

---

## Layout Patterns

### Chat Interface Layout

```tsx
function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main className="pb-32 pt-16">
        {children}
      </main>
      <ChatInput />
    </div>
  )
}
```

### Fixed Bottom Chat Input

```tsx
import { Send, Mic, Paperclip } from 'lucide-react';
import { useState } from 'react';

export function ChatInput({ onSend }: { onSend?: (message: string) => void }) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSend?.(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section className="w-full px-6 py-6 fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-3 bg-gray-50 rounded-2xl px-4 py-3 border border-gray-200 focus-within:border-blue-400 focus-within:bg-white transition-all">
          <button className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>

          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="flex-1 bg-transparent text-gray-900 placeholder-gray-400 outline-none text-base"
          />

          <button className="w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
            <Mic className="w-5 h-5" />
          </button>

          <button
            onClick={handleSend}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
              message.trim()
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-200 text-gray-400'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-3">
          AI can make mistakes. Consider checking important information.
        </p>
      </div>
    </section>
  );
}
```

### Navbar

```tsx
import { BookOpen } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="w-full px-6 py-4 flex items-center justify-between bg-white fixed top-0 left-0 right-0 z-50">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
          <BookOpen className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-semibold text-gray-900">AI Learning</span>
      </div>

      <div className="flex items-center gap-8">
        <a href="#" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
          Learn
        </a>
        <a href="#" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
          History
        </a>
      </div>
    </nav>
  );
}
```

### Message Area (Centered Content)

```tsx
export function MessageArea({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {children}
    </div>
  );
}
```

### Empty State

```tsx
import { Sparkles } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-6">
        <Sparkles className="w-8 h-8 text-blue-500" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        What would you like to learn?
      </h2>
      <p className="text-gray-500 max-w-md">
        Enter any topic below and I'll create a personalized learning experience with videos, quizzes, and explanations.
      </p>
    </div>
  );
}
```

---

## Animation Patterns

### Transitions

```css
/* Standard transition */
transition-all
transition-colors
transition-shadow

/* Duration */
duration-150  /* Fast */
duration-200  /* Normal */
duration-300  /* Slow */
```

### Focus States

Always use visible focus rings for accessibility:

```css
focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]
```

### Hover Effects

```css
/* Color change */
hover:text-gray-900
hover:bg-gray-100

/* Elevation */
hover:shadow-md

/* Scale */
hover:scale-105
```

---

## Best Practices

### Do's

1. Use HSL color variables for theming consistency
2. Always use the `cn()` utility for class merging
3. Keep components composable with slot patterns
4. Use semantic color names (`primary`, `destructive`, etc.)
5. Include focus-visible states for accessibility
6. Use transition classes for smooth interactions
7. Center content with `max-w-3xl mx-auto`

### Don'ts

1. Don't use arbitrary color values - use design tokens
2. Don't skip focus states on interactive elements
3. Don't use inline styles - use Tailwind classes
4. Don't hard-code spacing - use the spacing scale
5. Don't mix different border radius values arbitrarily

---

## Dependencies

Required packages for this design system:

```json
{
  "dependencies": {
    "@radix-ui/react-slot": "^1.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "lucide-react": "^0.400.0",
    "tailwind-merge": "^2.0.0"
  }
}
```
