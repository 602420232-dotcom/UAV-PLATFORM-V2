export class GeolocationService {
  constructor() {
    this.supported = 'geolocation' in navigator
    this.currentPosition = null
    this.watchId = null
    this.callbacks = []
  }

  async getCurrentPosition(options = {}) {
    if (!this.supported) {
      throw new Error('Geolocation is not supported by this browser')
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 0
    }

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          this.currentPosition = position
          resolve(position)
        },
        (error) => {
          reject(this._handleError(error))
        },
        { ...defaultOptions, ...options }
      )
    })
  }

  watchPosition(callback, options = {}) {
    if (!this.supported) {
      throw new Error('Geolocation is not supported by this browser')
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 30000
    }

    if (!this.callbacks.includes(callback)) {
      this.callbacks.push(callback)
    }

    if (!this.watchId) {
      this.watchId = navigator.geolocation.watchPosition(
        (position) => {
          this.currentPosition = position
          this.callbacks.forEach(cb => cb(position))
        },
        (error) => {
          const err = this._handleError(error)
          this.callbacks.forEach(cb => cb(null, err))
        },
        { ...defaultOptions, ...options }
      )
    }

    return this.watchId
  }

  clearWatch(watchId) {
    if (this.watchId && (!watchId || watchId === this.watchId)) {
      navigator.geolocation.clearWatch(this.watchId)
      this.watchId = null
    }
  }

  removeCallback(callback) {
    const index = this.callbacks.indexOf(callback)
    if (index > -1) {
      this.callbacks.splice(index, 1)
    }
    if (this.callbacks.length === 0 && this.watchId) {
      this.clearWatch()
    }
  }

  _handleError(error) {
    const errorMessages = {
      1: 'User denied Geolocation permission',
      2: 'Position unavailable',
      3: 'Timeout'
    }
    return new Error(errorMessages[error.code] || 'Unknown error')
  }

  formatPosition(position) {
    if (!position) return null
    return {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      altitude: position.coords.altitude,
      altitudeAccuracy: position.coords.altitudeAccuracy,
      heading: position.coords.heading,
      speed: position.coords.speed,
      timestamp: position.timestamp
    }
  }

  async getAddress(latitude, longitude) {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`
      )
      if (!response.ok) {
        throw new Error('Failed to fetch address')
      }
      const data = await response.json()
      
      // 检查返回数据是否有效
      if (!data || !data.address) {
        return null
      }
      
      return {
        displayName: data.display_name || '',
        address: data.address,
        formatted: this._formatAddress(data.address)
      }
    } catch (error) {
      console.warn('Failed to reverse geocode:', error)
      return null
    }
  }

  _formatAddress(address) {
    if (!address) return ''
    
    const parts = []
    // 优先使用市辖区
    if (address.city) parts.push(address.city)
    else if (address.county) parts.push(address.county)
    else if (address.town) parts.push(address.town)
    else if (address.village) parts.push(address.village)
    else if (address.municipality) parts.push(address.municipality)
    
    // 省份
    if (address.state) parts.push(address.state)
    else if (address.province) parts.push(address.province)
    
    // 国家
    if (address.country) parts.push(address.country)
    
    return parts.join(', ')
  }

  distanceBetween(lat1, lon1, lat2, lon2) {
    const R = 6371000
    const dLat = this._toRad(lat2 - lat1)
    const dLon = this._toRad(lon2 - lon1)
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this._toRad(lat1)) * Math.cos(this._toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c
  }

  _toRad(deg) {
    return deg * (Math.PI / 180)
  }

  getRegionByPosition(latitude, longitude) {
    if (latitude > 34 && latitude < 42 && longitude > 110 && longitude < 120) {
      return { name: '华北', key: 'north' }
    }
    if (latitude > 23 && latitude < 32 && longitude > 114 && longitude < 123) {
      return { name: '华东', key: 'east' }
    }
    if (latitude > 18 && latitude < 26 && longitude > 108 && longitude < 118) {
      return { name: '华南', key: 'south' }
    }
    return { name: '未知区域', key: 'unknown' }
  }

  getPositionBounds(region) {
    const bounds = {
      east: [[23, 114], [32, 123]],
      north: [[34, 110], [42, 120]],
      south: [[18, 108], [26, 118]]
    }
    return bounds[region] || [[20, 105], [40, 125]]
  }
}

export const geolocationService = new GeolocationService()

export async function getCurrentLocation() {
  if (!('geolocation' in navigator)) {
    return { success: false, error: 'Geolocation not supported' }
  }

  try {
    const position = await geolocationService.getCurrentPosition()
    const formatted = geolocationService.formatPosition(position)
    const address = await geolocationService.getAddress(
      formatted.latitude,
      formatted.longitude
    )
    const region = geolocationService.getRegionByPosition(
      formatted.latitude,
      formatted.longitude
    )

    return {
      success: true,
      position: formatted,
      address,
      region
    }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

export function watchLocation(callback) {
  if (!('geolocation' in navigator)) {
    callback({ success: false, error: 'Geolocation not supported' })
    return null
  }

  return geolocationService.watchPosition(async (position, error) => {
    if (error) {
      callback({ success: false, error: error.message })
      return
    }

    const formatted = geolocationService.formatPosition(position)
    const address = await geolocationService.getAddress(
      formatted.latitude,
      formatted.longitude
    )
    const region = geolocationService.getRegionByPosition(
      formatted.latitude,
      formatted.longitude
    )

    callback({
      success: true,
      position: formatted,
      address,
      region
    })
  })
}
