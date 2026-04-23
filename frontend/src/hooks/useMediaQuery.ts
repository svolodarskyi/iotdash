import { useEffect, useState } from 'react'
import { breakpoints } from '../lib/breakpoints'

/**
 * Hook to check if a media query matches
 *
 * @param query - CSS media query string (e.g., "(max-width: 767px)")
 * @returns boolean indicating if the media query matches
 *
 * @example
 * const isMobile = useMediaQuery('(max-width: 767px)')
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches
    }
    return false
  })

  useEffect(() => {
    const media = window.matchMedia(query)

    // Update state if it doesn't match current media query state
    if (media.matches !== matches) {
      setMatches(media.matches)
    }

    const listener = () => setMatches(media.matches)

    // Modern browsers support addEventListener
    media.addEventListener('change', listener)

    return () => media.removeEventListener('change', listener)
  }, [matches, query])

  return matches
}

/**
 * Hook to detect mobile viewport (< md breakpoint)
 * Corresponds to Tailwind's md breakpoint (768px)
 */
export const useIsMobile = () => useMediaQuery(`(max-width: ${breakpoints.tablet - 1}px)`)

/**
 * Hook to detect tablet viewport (md to lg breakpoints)
 * Between Tailwind's md (768px) and lg (1024px) breakpoints
 */
export const useIsTablet = () => useMediaQuery(`(min-width: ${breakpoints.tablet}px) and (max-width: ${breakpoints.desktop - 1}px)`)

/**
 * Hook to detect desktop viewport (>= lg breakpoint)
 * Corresponds to Tailwind's lg breakpoint (1024px) and above
 */
export const useIsDesktop = () => useMediaQuery(`(min-width: ${breakpoints.desktop}px)`)
