/**
 * Responsive breakpoint constants
 *
 * These breakpoints align with common device sizes and Tailwind's default breakpoints.
 *
 * Tailwind built-in breakpoints:
 * - sm: 640px
 * - md: 768px
 * - lg: 1024px
 * - xl: 1280px
 * - 2xl: 1536px
 */
export const breakpoints = {
  mobile: 320,      // Small phones (iPhone SE)
  mobileLarge: 375, // Standard phones (iPhone 12/13)
  tablet: 768,      // iPad and tablets
  desktop: 1024,    // Desktop screens
  wide: 1280,       // Wide desktop screens
} as const

export type Breakpoint = keyof typeof breakpoints
