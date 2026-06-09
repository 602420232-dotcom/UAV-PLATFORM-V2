import { ref, onMounted, onBeforeUnmount } from 'vue'

const DEFAULT_COORDS = { lat: 39.9, lng: 116.4 }
const SUNRISE_HOUR_LOCAL = 6
const SUNSET_HOUR_LOCAL = 19

function getLocalHours(ts = Date.now()) {
  return new Date(ts).getHours() + new Date(ts).getMinutes() / 60
}

function isNightTime(ts = Date.now()) {
  const h = getLocalHours(ts)
  return h < SUNRISE_HOUR_LOCAL || h >= SUNSET_HOUR_LOCAL
}

function nextTransitionSeconds(ts = Date.now()) {
  const now = new Date(ts)
  const h = now.getHours()
  const m = now.getMinutes()
  const s = now.getSeconds()
  const currentMinutes = h * 60 + m + s / 60

  const sunriseMin = SUNRISE_HOUR_LOCAL * 60
  const sunsetMin = SUNSET_HOUR_LOCAL * 60
  const dayMinutes = 24 * 60

  let nextMin
  if (currentMinutes < sunriseMin) {
    nextMin = sunriseMin
  } else if (currentMinutes < sunsetMin) {
    nextMin = sunsetMin
  } else {
    nextMin = sunriseMin + dayMinutes
  }
  return Math.max(1, Math.round((nextMin - currentMinutes) * 60))
}

async function fetchUserCoords() {
  if (typeof navigator === 'undefined' || !navigator.geolocation) {
    return DEFAULT_COORDS
  }
  try {
    return await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => reject(new Error('geolocation denied')),
        { timeout: 3000, maximumAge: 600000 }
      )
    })
  } catch (e) {
    return DEFAULT_COORDS
  }
}

export function useSunTime({ reactive = true } = {}) {
  const coords = reactive ? ref({ ...DEFAULT_COORDS }) : { ...DEFAULT_COORDS }
  const night = reactive ? ref(isNightTime()) : isNightTime()
  let pollingTimer = null

  function refresh() {
    const val = isNightTime()
    if (reactive) night.value = val
    return val
  }

  function scheduleNext() {
    const seconds = Math.min(nextTransitionSeconds(), 3600)
    if (pollingTimer) clearTimeout(pollingTimer)
    pollingTimer = setTimeout(() => {
      refresh()
      scheduleNext()
    }, seconds * 1000)
  }

  onMounted(async () => {
    const c = await fetchUserCoords()
    if (reactive) coords.value = c
    refresh()
    scheduleNext()
  })

  onBeforeUnmount(() => {
    if (pollingTimer) clearTimeout(pollingTimer)
  })

  return {
    coords,
    isNightTime: (ts) => (ts !== undefined ? isNightTime(ts) : (reactive ? night.value : night)),
    night,
    nextTransitionSeconds,
    refresh
  }
}

export { isNightTime, nextTransitionSeconds, SUNRISE_HOUR_LOCAL, SUNSET_HOUR_LOCAL }
