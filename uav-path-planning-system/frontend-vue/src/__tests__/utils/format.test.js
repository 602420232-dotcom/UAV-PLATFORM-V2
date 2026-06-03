import { describe, it, expect } from 'vitest'

// Common utility functions that should exist in the app
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toISOString().split('T')[0]
}

const formatDateTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const roundTo = (num, decimals = 2) => {
  if (num === null || num === undefined) return 0
  return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals)
}

const isValidCoordinate = (lat, lng) => {
  return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
}

const calculateDistance = (lat1, lng1, lat2, lng2) => {
  const R = 6371000
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

describe('Utility Functions', () => {
  describe('formatDate', () => {
    it('should format a date correctly', () => {
      expect(formatDate('2026-06-03T10:30:00Z')).toBe('2026-06-03')
    })
    it('should return empty string for null', () => {
      expect(formatDate(null)).toBe('')
    })
    it('should return empty string for undefined', () => {
      expect(formatDate(undefined)).toBe('')
    })
  })

  describe('formatDateTime', () => {
    it('should format date time for Chinese locale', () => {
      const result = formatDateTime('2026-06-03T10:30:00Z')
      expect(result).toBeTruthy()
      expect(result).toContain('2026')
    })
  })

  describe('roundTo', () => {
    it('should round to 2 decimal places by default', () => {
      expect(roundTo(3.14159)).toBe(3.14)
    })
    it('should round to specified decimals', () => {
      expect(roundTo(3.14159, 3)).toBe(3.142)
    })
    it('should return 0 for null', () => {
      expect(roundTo(null)).toBe(0)
    })
    it('should return 0 for undefined', () => {
      expect(roundTo(undefined)).toBe(0)
    })
  })

  describe('isValidCoordinate', () => {
    it('should accept valid coordinates', () => {
      expect(isValidCoordinate(31.23, 121.47)).toBe(true)
    })
    it('should reject invalid latitude', () => {
      expect(isValidCoordinate(100, 121.47)).toBe(false)
    })
    it('should reject invalid longitude', () => {
      expect(isValidCoordinate(31.23, 200)).toBe(false)
    })
  })

  describe('calculateDistance', () => {
    it('should return 0 for same point', () => {
      expect(calculateDistance(31.23, 121.47, 31.23, 121.47)).toBe(0)
    })
    it('should calculate distance between two points', () => {
      // Shanghai to Beijing ~1060km
      const dist = calculateDistance(31.23, 121.47, 39.90, 116.40)
      expect(dist).toBeGreaterThan(1000000)
      expect(dist).toBeLessThan(1200000)
    })
  })
})
