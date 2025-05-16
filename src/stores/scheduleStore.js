import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useScheduleStore = defineStore('schedule', () => {
  const schedules = ref([])
  const loading = ref(false)

  async function fetchSchedules (BACKEND_URL) {
    loading.value = true
    try {
      const res = await fetch(`${BACKEND_URL}/api/state`)
      const data = await res.json()
      if (data.scheduleData && Array.isArray(data.scheduleData.schedules)) {
        const lightOrder = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
        schedules.value = data.scheduleData.schedules.map(arr => ({
          enabled: arr[0],
          start: toTimeString(arr[1]),
          end: toTimeString(arr[2]),
          lights: lightOrder.filter((l, i) => arr[3 + i]),
          title: 'Untitled Schedule',
        }))
      } else {
        schedules.value = []
      }
    } finally {
      loading.value = false
    }
  }

  function toTimeString (military) {
    if (!military && military !== 0) return null
    let h = Math.floor(military / 100)
    const m = military % 100
    let ampm = 'AM'
    if (h === 0) h = 12
    else if (h === 12) ampm = 'PM'
    else if (h > 12) { h -= 12; ampm = 'PM' }
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${ampm}`
  }

  return { schedules, loading, fetchSchedules }
})
