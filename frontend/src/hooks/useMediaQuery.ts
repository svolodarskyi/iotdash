import { useEffect, useState } from 'react'

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
 * Hook to detect mobile viewport (< 768px)
 * Corresponds to Tailwind's md breakpoint
 */
export const useIsMobile = () => useMediaQuery('(max-width: 767px)')

/**
 * Hook to detect tablet viewport (768px - 1023px)
 * Between Tailwind's md and lg breakpoints
 */
export const useIsTablet = () => useMediaQuery('(min-width: 768px) and (max-width: 1023px)')

/**
 * Hook to detect desktop viewport (>= 1024px)
 * Corresponds to Tailwind's lg breakpoint and above
 */
export const useIsDesktop = () => useMediaQuery('(min-width: 1024px)')
