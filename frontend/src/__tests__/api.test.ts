import { describe, it, expect } from 'vitest'
import { rewriteGrafanaUrl } from '../lib/api'

// Mock the env var — VITE_GRAFANA_URL defaults to http://localhost:3000
// since import.meta.env.VITE_GRAFANA_URL is undefined in test

describe('rewriteGrafanaUrl', () => {
  it('rewrites Docker-internal grafana URL to localhost', () => {
    const input = 'http://grafana:3000/d-solo/abc123?orgId=1&panelId=2&var-device_id=sensor01'
    const result = rewriteGrafanaUrl(input)
    expect(result).toBe(
      'http://localhost:3000/d-solo/abc123?orgId=1&panelId=2&var-device_id=sensor01',
    )
  })

  it('preserves URLs that do not match the grafana internal pattern', () => {
    const input = 'http://example.com/some-path?foo=bar'
    const result = rewriteGrafanaUrl(input)
    expect(result).toBe('http://example.com/some-path?foo=bar')
  })

  it('only rewrites the http://grafana:3000 prefix', () => {
    const input = 'http://grafana:3000/d-solo/uid?orgId=1'
    const result = rewriteGrafanaUrl(input)
    expect(result).toContain('/d-solo/uid?orgId=1')
    expect(result).not.toContain('grafana:3000')
  })

  it('does not rewrite grafana:3000 appearing in query params', () => {
    const input = 'http://localhost:8000/api?ref=http://grafana:3000/foo'
    const result = rewriteGrafanaUrl(input)
    // Only prefix should be replaced, not mid-string occurrences
    expect(result).toBe('http://localhost:8000/api?ref=http://grafana:3000/foo')
  })
})
