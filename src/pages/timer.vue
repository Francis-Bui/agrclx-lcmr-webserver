<template>
  <v-container class="fill-height d-flex flex-column align-center justify-center">
    <!-- Schedules List -->
    <div v-if="schedules.length > 0" class="w-100 d-flex flex-column align-center">
      <v-card
        v-for="(schedule, idx) in schedules"
        :key="schedule.id"
        class="mb-4"
        elevation="4"
        style="cursor:pointer; position:relative;"
        width="400"
        @click="editSchedule(idx)"
      >
        <v-card-title class="d-flex justify-space-between align-center">
          <span>{{ schedule.title }}</span>
          <v-switch
            v-model="schedule.enabled"
            :color="schedule.enabled ? 'success' : 'error'"
            hide-details
            @click.stop
          />
        </v-card-title>
        <v-card-text>
          <div class="mb-2">
            <strong>Start:</strong> {{ formatTime(schedule.start) }}<br>
            <strong>End:</strong> {{ formatTime(schedule.end) }}
          </div>
          <v-chip-group column multiple>
            <v-chip
              v-for="light in schedule.lights"
              :key="light"
              class="ma-1"
              color="primary"
            >{{ light }}</v-chip>
          </v-chip-group>
        </v-card-text>
      </v-card>
      <!-- Add Schedule Button -->
      <v-btn
        class="my-8"
        color="primary"
        size="x-large"
        style="border-radius:50%; width:80px; height:80px;"
        variant="tonal"
        @click="openCreateDialog"
      >
        <v-icon size="48">mdi-plus</v-icon>
      </v-btn>
    </div>

    <!-- No Schedules: Big Plus -->
    <div v-else class="d-flex flex-column align-center justify-center">
      <v-btn
        color="primary"
        size="x-large"
        style="border-radius:50%; width:120px; height:120px;"
        variant="tonal"
        @click="openCreateDialog"
      >
        <v-icon size="64">mdi-plus</v-icon>
      </v-btn>
    </div>

    <!-- Create Schedule Dialog -->
    <v-dialog v-model="createDialog" max-width="400" persistent>
      <v-card>
        <v-card-title>Create Schedule?</v-card-title>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="startScheduleCreation">Yes</v-btn>
          <v-btn @click="createDialog = false">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit/Create Schedule Dialog -->
    <v-dialog v-model="editDialog" max-width="400" persistent>
      <v-card>
        <v-card-title>
          <v-text-field
            v-model="editScheduleData.title"
            hide-details
            label="Title"
            style="font-size:1.2em;"
            variant="plain"
          />
        </v-card-title>
        <v-card-text>
          <div class="mb-2 d-flex flex-column align-center">
            <div class="d-flex align-center mb-2" style="gap: 12px;">
              <span>Start:</span>
              <v-btn
                color="success"
                style="min-width:80px;"
                variant="outlined"
                @click="showTimePicker('start')"
              >
                {{ editScheduleData.start ? formatTime(editScheduleData.start) : 'Set Time' }}
              </v-btn>
            </div>
            <div class="d-flex align-center mb-2" style="gap: 12px;">
              <span>End:</span>
              <v-btn
                color="error"
                style="min-width:80px;"
                variant="outlined"
                @click="showTimePicker('end')"
              >
                {{ editScheduleData.end ? formatTime(editScheduleData.end) : 'Set Time' }}
              </v-btn>
            </div>
            <v-chip-group
              v-model="editScheduleData.lights"
              class="mb-2 d-flex flex-wrap justify-center"
              column
              multiple
            >
              <v-chip
                v-for="light in lights"
                :key="light"
                class="ma-1"
                color="primary"
                size="small"
                :value="light"
                :variant="editScheduleData.lights.includes(light) ? 'elevated' : 'outlined'"
              >
                {{ light }}
              </v-chip>
            </v-chip-group>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="editingIdx !== null"
            class="mr-auto"
            color="error"
            variant="tonal"
            @click="deleteSchedule(editingIdx)"
          >
            <v-icon start>mdi-delete</v-icon>
            Delete
          </v-btn>
          <v-spacer />
          <v-btn
            color="primary"
            :disabled="!canSave"
            @click="saveSchedule"
          >Save</v-btn>
          <v-btn @click="closeEditDialog">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Time Picker Dialog -->
    <v-dialog v-model="timePickerDialog.visible" max-width="320" persistent>
      <v-card>
        <v-time-picker
          v-model="timePickerDialog.time"
          :color="timePickerDialog.type === 'start' ? 'success' : 'error'"
          format="ampm"
          full-width
        />
        <v-card-actions>
          <v-btn
            class="px-4"
            rounded="lg"
            variant="outlined"
            @click="toggleAMPM"
          >
            {{ timePickerDialog.ampm }}
          </v-btn>
          <v-spacer />
          <v-btn color="primary" @click="confirmTimePicker">OK</v-btn>
          <v-btn @click="timePickerDialog.visible = false">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Conflict Warning Dialog -->
    <v-dialog v-model="conflictDialog.visible" max-width="400" persistent>
      <v-card>
        <v-card-title>Schedule Conflict</v-card-title>
        <v-card-text>
          <div>
            This schedule with <strong>{{ conflictDialog.chip }}</strong> overlaps with <strong>{{ conflictDialog.conflictTitle }}</strong>!<br>
            Overlapping time: {{ conflictDialog.overlap }}
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="conflictDialog.visible = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Bottom Navigation -->
    <v-bottom-navigation
      class="mt-8"
      color="primary"
      grow
      mode="fixed"
      style="border-radius: 0 0 12px 12px;"
    >
      <v-btn :active="$route.path === '/'" icon to="/">
        <v-icon>mdi-lightbulb-outline</v-icon>
        <span>Light</span>
      </v-btn>
      <v-btn :active="$route.path === '/timer'" icon to="/timer">
        <v-icon>mdi-timer-outline</v-icon>
        <span>Timer</span>
      </v-btn>
      <v-btn :active="$route.path === '/data'" icon to="/data">
        <v-icon>mdi-database-outline</v-icon>
        <span>Data</span>
      </v-btn>
    </v-bottom-navigation>
  </v-container>
</template>

<script setup>
  import { computed, onMounted, reactive, ref, watch } from 'vue'

  const lights = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']

  const BACKEND_URL = 'http://192.168.0.148:5000' // Device IP address

  const schedules = ref([]) // {id, title, start, end, lights, enabled}
  const createDialog = ref(false)
  const editDialog = ref(false)
  const editingIdx = ref(null)
  const editScheduleData = reactive({
    id: null,
    title: 'Untitled Schedule',
    start: null,
    end: null,
    lights: [],
    enabled: true,
  })

  const timePickerDialog = reactive({
    visible: false,
    type: 'start',
    time: null,
    ampm: 'AM',
  })

  const conflictDialog = reactive({
    visible: false,
    chip: '',
    conflictTitle: '',
    overlap: '',
  })

  // Persistence: Load from localStorage on mount, save on change
  onMounted(() => {
    const saved = localStorage.getItem('schedules')
    if (saved) schedules.value = JSON.parse(saved)
  })
  watch(schedules, val => {
    localStorage.setItem('schedules', JSON.stringify(val))
  }, { deep: true })

  // Change formatting to simplify backend processing
  function formatSchedulesForBackend (schedules) {
    // Light order: IR, R, G, B, W, UV
    const lightOrder = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']

    function toMilitaryTime (str) {
      if (!str) return 0
      let [h, m, ampm] = str.split(':')
      h = parseInt(h)
      m = parseInt(m)
      if (ampm === 'PM' && h !== 12) h += 12
      if (ampm === 'AM' && h === 12) h = 0
      return (h * 100) + m
    }

    return schedules.map(s => [
      !!s.enabled,
      toMilitaryTime(s.start),
      toMilitaryTime(s.end),
      ...lightOrder.map(light => s.lights && s.lights.includes(light)),
    ])
  }

  // Get lighting values from local storage to prevent sending null values
  function getLightingFromStorage () {
    // Should match the order [IR, R, G, B, W, UV]
    const order = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
    const saved = JSON.parse(localStorage.getItem('lightSliderValues') || '{}')
    return order.map(k => Number(saved[k]) || 0)
  }

  async function sendStateToBackend (lighting, scheduleData) {
    const response = await fetch(`${BACKEND_URL}/api/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lighting,
        scheduleData,
      }),
    })
    const result = await response.json()
    console.log('Backend response:', result) // Debug print
  }

  function openCreateDialog () {
    createDialog.value = true
  }
  function startScheduleCreation () {
    createDialog.value = false
    openEditDialog()
  }
  function openEditDialog (idx = null) {
    editDialog.value = true
    editingIdx.value = idx
    if (idx === null) {
      // New
      Object.assign(editScheduleData, {
        id: Date.now(),
        title: 'Untitled Schedule',
        start: null,
        end: null,
        lights: [],
        enabled: true,
      })
    } else {
      // Edit existing
      Object.assign(editScheduleData, JSON.parse(JSON.stringify(schedules.value[idx])))
    }
  }
  function closeEditDialog () {
    editDialog.value = false
    editingIdx.value = null
  }
  function editSchedule (idx) {
    openEditDialog(idx)
  }
  function deleteSchedule (idx) {
    schedules.value.splice(idx, 1)
    closeEditDialog()
    sendStateToBackend(
      getLightingFromStorage(), // <-- see below
      {
        scheduleCount: schedules.value.length,
        schedules: formatSchedulesForBackend(schedules.value),
      }
    )
  }
  function showTimePicker (type) {
    timePickerDialog.type = type
    timePickerDialog.visible = true
    const t = editScheduleData[type]
    if (t) {
      const [h, m, ampm] = t.split(':')
      timePickerDialog.time = `${h.padStart(2, '0')}:${m.padStart(2, '0')}`
      timePickerDialog.ampm = ampm
    } else {
      timePickerDialog.time = '12:00'
      timePickerDialog.ampm = 'AM'
    }
  }
  function toggleAMPM () {
    timePickerDialog.ampm = timePickerDialog.ampm === 'AM' ? 'PM' : 'AM'
  }
  function confirmTimePicker () {
    let [h, m] = timePickerDialog.time.split(':').map(Number)
    const ampm = timePickerDialog.ampm

    // Convert 24h to 12h based on AM/PM toggle
    if (ampm === 'AM') {
      if (h === 0) h = 12
      if (h > 12) h -= 12
    } else { // PM
      if (h === 0) h = 12
      if (h < 12) h += 12
      if (h > 12) h -= 12 // Prevent 24h overflow
    }

    // Always store as 2-digit hour
    editScheduleData[timePickerDialog.type] = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${ampm}`
    timePickerDialog.visible = false
  }
  function formatTime (val) {
    if (!val) return '--:--'
    const [h, m, ampm] = val.split(':')
    return `${h.padStart(2, '0')}:${m.padStart(2, '0')} ${ampm}`
  }
  const canSave = computed(() =>
    editScheduleData.title &&
    editScheduleData.start &&
    editScheduleData.end &&
    editScheduleData.lights.length > 0
  )

  function saveSchedule () {
    // Conflict check
    for (let i = 0; i < schedules.value.length; i++) {
      if (editingIdx.value !== null && i === editingIdx.value) continue
      const s = schedules.value[i]
      for (const light of editScheduleData.lights) {
        if (s.lights.includes(light)) {
          // Check time overlap
          if (timesOverlap(editScheduleData.start, editScheduleData.end, s.start, s.end)) {
            conflictDialog.chip = light
            conflictDialog.conflictTitle = s.title
            conflictDialog.overlap = `${formatTime(s.start)} - ${formatTime(s.end)}`
            conflictDialog.visible = true
            return
          }
        }
      }
    }
    if (editingIdx.value === null) {
      schedules.value.push(JSON.parse(JSON.stringify(editScheduleData)))
    } else {
      schedules.value[editingIdx.value] = JSON.parse(JSON.stringify(editScheduleData))
    }
    closeEditDialog()
    sendStateToBackend(
      getLightingFromStorage(), // <-- see below
      {
        scheduleCount: schedules.value.length,
        schedules: formatSchedulesForBackend(schedules.value),
      }
    )
  }
  function timesOverlap (start1, end1, start2, end2) {
    // Convert to minutes since midnight
    const toMin = t => {
      let [h, m, ampm] = t.split(':')
      h = parseInt(h)
      m = parseInt(m)
      if (ampm === 'PM' && h !== 12) h += 12
      if (ampm === 'AM' && h === 12) h = 0
      return h * 60 + m
    }
    const s1 = toMin(start1), e1 = toMin(end1), s2 = toMin(start2), e2 = toMin(end2)
    return Math.max(s1, s2) < Math.min(e1, e2)
  }
</script>
