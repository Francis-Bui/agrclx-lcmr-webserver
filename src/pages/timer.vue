<template>
  <div class="page-root">
    <v-container class="fill-height d-flex flex-column align-center justify-center">
      <!-- Schedules List -->
      <div v-if="schedules.length > 0" class="schedule-list-scroll">
        <v-row class="w-100" dense>
          <v-col
            v-for="(schedule, idx) in schedules"
            :key="schedule.id"
            class="d-flex justify-center"
            cols="12"
            sm="6"
          >
            <v-card
              class="mb-4 schedule-card"
              elevation="6"
              style="border-radius: 24px; position:relative;"
            >
              <div class="d-flex justify-space-between align-center px-4 pt-3">
                <span class="schedule-title">{{ schedule.title }}</span>
                <v-switch
                  v-model="schedule.enabled"
                  class="schedule-switch"
                  :color="schedule.enabled ? 'success' : 'error'"
                  hide-details
                  @change="onScheduleSwitchChange(schedule)"
                  @click.stop
                />
              </div>
              <div class="d-flex flex-row align-center px-4 pb-2 pt-1" style="gap: 24px;">
                <div class="d-flex flex-column align-start" style="min-width:120px;">
                  <div><strong>Start:</strong> {{ formatTime(schedule.start) }}</div>
                  <div><strong>End:</strong> {{ formatTime(schedule.end) }}</div>
                </div>
                <div class="flex-grow-1 d-flex align-center justify-center">
                  <div class="profile-bar schedule-bar-graph">
                    <div
                      v-for="(val, i) in schedule.profile_values"
                      :key="lights[i]"
                      class="profile-bar-mini"
                      :style="{ background: chipColors[lights[i]], height: (val || 0) + '%', opacity: 0.85 }"
                    />
                  </div>
                </div>
              </div>
              <div class="d-flex flex-row justify-space-between align-center px-4 pb-3 pt-1">
                <v-btn
                  class="schedule-action-btn"
                  color="error"
                  variant="tonal"
                  @click.stop="deleteScheduleHandler(idx)"
                >
                  <v-icon start>mdi-delete</v-icon>
                  Delete
                </v-btn>
                <v-btn
                  class="schedule-action-btn"
                  color="primary"
                  variant="tonal"
                  @click.stop="editSchedule(idx)"
                >
                  <v-icon start>mdi-pencil</v-icon>
                  Edit
                </v-btn>
              </div>
            </v-card>
          </v-col>
        </v-row>
        <!-- Add Schedule Button -->
        <div class="d-flex justify-center my-8">
          <v-btn
            color="primary"
            size="x-large"
            style="border-radius:50%; width:80px; aspect-ratio:1/1;"
            variant="tonal"
            @click="openCreateDialog"
          >
            <v-icon size="48">mdi-plus</v-icon>
          </v-btn>
        </div>
      </div>

      <!-- No Schedules: Big Plus -->
      <div v-else class="d-flex flex-column align-center justify-center">
        <v-btn
          color="primary"
          size="x-large"
          style="border-radius:50%; width:120px; aspect-ratio:1/1; min-width:0; min-height:0; height:auto;"
          variant="tonal"
          @click="openCreateDialog"
        >
          <v-icon color="#bdbdbd" size="48">mdi-plus</v-icon>
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
              <div class="d-flex flex-column align-center mb-2" style="gap: 12px; width: 100%;">
                <div class="d-flex flex-row align-center justify-center" style="gap: 12px; width: 100%;">
                  <span style="min-width: 48px; text-align: left; font-weight: 500;">Start:</span>
                  <v-btn
                    color="success"
                    style="min-width:100px; margin: 0 auto;"
                    variant="outlined"
                    @click="showTimePicker('start')"
                  >
                    {{ editScheduleData.start ? formatTime(editScheduleData.start) : 'Set Time' }}
                  </v-btn>
                </div>
                <div class="d-flex flex-row align-center justify-center" style="gap: 12px; width: 100%;">
                  <span style="min-width: 48px; text-align: left; font-weight: 500;">End:</span>
                  <v-btn
                    color="error"
                    style="min-width:100px; margin: 0 auto;"
                    variant="outlined"
                    @click="showTimePicker('end')"
                  >
                    {{ editScheduleData.end ? formatTime(editScheduleData.end) : 'Set Time' }}
                  </v-btn>
                </div>
              </div>
              <div class="d-flex flex-column align-center mb-2" style="width: 100%;">
                <span class="mb-1" style="align-self: flex-start;">Profile:</span>
                <div style="width: 100%; display: flex; justify-content: center;">
                  <div v-if="!editScheduleData.profile_name" class="profile-card-blank" @click="profilePickerDialog = true">
                    <v-icon color="#bdbdbd" size="48">mdi-plus</v-icon>
                  </div>
                  <div v-else class="profile-card-selected" @click="profilePickerDialog = true">
                    <div class="profile-title-center" style="margin-bottom: 0;">{{ editScheduleData.profile_name }}</div>
                    <div class="profile-preview profile-preview-center mt-2">
                      <div
                        v-for="(val, idx) in editScheduleData.profile_values"
                        :key="lights[idx]"
                        class="profile-bar-mini"
                        :style="{ background: chipColors[lights[idx]], height: (val || 0) + '%', opacity: 0.85 }"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-btn
              v-if="editingIdx !== null"
              class="mr-auto"
              color="error"
              variant="tonal"
              @click="deleteScheduleHandler(editingIdx)"
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

      <!-- Profile Picker Dialog for Schedules (EXACT MATCH TO index.vue) -->
      <v-dialog v-model="profilePickerDialog" max-width="600" persistent>
        <v-card>
          <v-card-title>Select Profile</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="profile in profiles"
                :key="profile.name"
                class="profile-list-item profile-list-item-rounded"
                :class="{'selected-profile': profile.name === editScheduleData.profile_name}"
                elevation="4"
                style="max-width:340px;margin:16px auto 0 auto;position:relative;"
                @click="selectProfileForSchedule(profile)"
              >
                <v-list-item-content>
                  <v-list-item-title class="profile-title-center">{{ profile.name }}</v-list-item-title>
                  <div class="profile-preview profile-preview-center">
                    <div
                      v-for="(val, idx) in profile.values"
                      :key="lights[idx]"
                      class="profile-bar-mini"
                      :style="{ background: chipColors[lights[idx]], height: (val || 0) + '%', opacity: 0.8 }"
                    />
                  </div>
                </v-list-item-content>
                <!-- Delete icon: middle left -->
                <v-btn
                  class="profile-action-btn profile-action-btn-delete"
                  color="error"
                  icon
                  style="position:absolute;top:50%;transform:translateY(-50%);z-index:2;"
                  variant="tonal"
                  @click.stop="deleteProfileHandler(profile)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="profilePickerDialog = false">Close</v-btn>
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
    </v-container>
  </div>
</template>

<script setup>
  import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
  import { useGlobalState } from '@/plugins/globalState'

  const lights = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
  const BACKEND_URL = `http://${window.location.hostname}:8080`

  const {
    schedules,
    profiles,
    fetchSchedules,
    fetchProfiles,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    deleteProfile,
    showAlert,
  } = useGlobalState()

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
    profile_name: '',
    profile_values: {},
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

  const chipColors = {
    IR: '#b71c1c',
    Red: '#ff5252',
    Green: '#4caf50',
    Blue: '#2196f3',
    White: '#bdbdbd',
    UV: '#7c4dff',
  }

  const profilePickerDialog = ref(false)

  onMounted(() => {
    fetchSchedules(BACKEND_URL)
    fetchProfiles(BACKEND_URL)
  })

  onUnmounted(() => {
  })

  function formatTime (val) {
    if (!val) return '--:--'
    const [h, m, ampm] = val.split(':')
    return `${h.padStart(2, '0')}:${m.padStart(2, '0')} ${ampm}`
  }

  const canSave = computed(() =>
    editScheduleData.title &&
    editScheduleData.start &&
    editScheduleData.end &&
    editScheduleData.profile_name
  )

  function timesOverlap (start1, end1, start2, end2) {
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
      Object.assign(editScheduleData, {
        id: Date.now(),
        title: 'Untitled Schedule',
        start: null,
        end: null,
        lights: [],
        enabled: true,
        profile_name: '',
        profile_values: {},
      })
    } else {
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
  async function deleteScheduleHandler (idx) {
    const schedule = schedules.value[idx]
    await deleteSchedule(schedule.id, BACKEND_URL)
    await fetchSchedules(BACKEND_URL)
    closeEditDialog()
    showAlert('Schedule deleted', 'success')
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
    if (ampm === 'AM') {
      if (h === 0) h = 12
      if (h > 12) h -= 12
    } else {
      if (h === 0) h = 12
      if (h < 12) h += 12
      if (h > 12) h -= 12
    }
    editScheduleData[timePickerDialog.type] = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${ampm}`
    timePickerDialog.visible = false
  }
  function onScheduleSwitchChange (schedule) {
    updateSchedule(schedule, BACKEND_URL)
    showAlert('Schedule updated', 'success')
  }
  async function saveSchedule () {
    for (let i = 0; i < schedules.value.length; i++) {
      if (editingIdx.value !== null && i === editingIdx.value) continue
      const s = schedules.value[i]
      for (const light of editScheduleData.lights) {
        if (s.lights.includes(light)) {
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
    const selectedProfile = profiles.value.find(p => p.name === editScheduleData.profile_name)
    if (!selectedProfile) {
      showAlert('Please select a profile', 'error')
      return
    }
    editScheduleData.profile_values = [...selectedProfile.values]
    if (editingIdx.value === null) {
      await createSchedule({ ...editScheduleData }, BACKEND_URL)
      showAlert('Schedule created', 'success')
    } else {
      await updateSchedule({ ...editScheduleData }, BACKEND_URL)
      showAlert('Schedule updated', 'success')
    }
    await fetchSchedules(BACKEND_URL)
    closeEditDialog()
  }
  function selectProfileForSchedule (profile) {
    editScheduleData.profile_name = profile.name
    editScheduleData.profile_values = [...profile.values]
    profilePickerDialog.value = false
  }
  function deleteProfileHandler (profile) {
    deleteProfile(profile.name, BACKEND_URL)
      .then(() => fetchProfiles(BACKEND_URL))
      .then(() => showAlert('Profile deleted', 'success'))
      .catch(() => showAlert('Failed to delete profile', 'error'))
  }
</script>

<style scoped>
/* Make all round v-btns truly circular */
.v-btn[style*="aspect-ratio"] {
  min-width: 0 !important;
  min-height: 0 !important;
  height: auto !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.schedule-card {
  border-radius: 24px !important;
  box-shadow: 0 8px 32px 0 rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.12);
  background: #fff;
  transition: box-shadow 0.2s, background 0.2s;
  margin-bottom: 0;
  min-width: 320px;
  max-width: 420px;
  width: 100%;
}
.schedule-card:hover {
  box-shadow: 0 12px 40px 0 rgba(0,0,0,0.22), 0 4px 16px rgba(0,0,0,0.14);
  background: #f7fafd;
}
.schedule-title {
  font-size: 1.2em;
  font-weight: bold;
  color: #222;
  letter-spacing: 0.5px;
}
.schedule-switch {
  margin-left: 8px;
}
.schedule-bar-graph {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  height: 38px;
  gap: 3px;
  margin-top: 0;
  margin-bottom: 0;
}
.profile-bar-mini {
  width: 14px;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}
.schedule-action-btn {
  min-width: 0;
  border-radius: 12px !important;
  font-weight: 500;
  font-size: 1em;
  padding: 0 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.selected-profile {
  background: #e3f2fd !important;
  border: 2px solid #1976d2 !important;
}
.profile-list-item {
  background: #fff;
  border-radius: 18px;
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.13);
  transition: box-shadow 0.2s;
  min-width: 0;
  width: 340px;
  max-width: 340px;
  padding: 0 0 0 0;
}
.profile-list-item-rounded {
  border-radius: 24px !important;
}
.profile-list-item:hover {
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.profile-action-btn {
  min-width: 0;
  width: 40px;
  height: 40px;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  padding: 0;
}
.profile-action-btn-delete {
  background: #fff !important;
  border: 2px solid #ff5252 !important;
}
.profile-title-center {
  text-align: center;
  width: 100%;
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 2px;
  margin-top: 2px;
}
.profile-preview {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  height: 36px;
  gap: 2px;
  margin-top: 8px;
  margin-bottom: 4px;
}
.profile-preview-center {
  justify-content: center;
  align-items: flex-end;
  display: flex;
  margin: 0 auto;
}
.profile-bar-mini {
  width: 10px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
}
.schedule-list-scroll {
  max-height: 80vh;
  overflow-y: auto;
  padding: 24px 0 0 0;
}
.v-row.w-100 {
  margin-left: auto !important;
  margin-right: auto !important;
  row-gap: 32px;
  column-gap: 0;
  max-width: 900px;
  justify-content: center;
}
.v-col.d-flex.justify-center {
  padding-left: 24px !important;
  padding-right: 24px !important;
  box-sizing: border-box;
}
.profile-card-blank {
  width: 220px;
  height: 64px;
  border-radius: 18px;
  background: #f3f3f3;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  margin: 0 auto 8px auto;
  transition: background 0.2s;
}
.profile-card-blank:hover {
  background: #e0e0e0;
}
.profile-card-selected {
  width: 220px;
  min-height: 64px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin: 0 auto 8px auto;
  padding: 8px 0 4px 0;
  transition: box-shadow 0.2s, background 0.2s;
}
.profile-card-selected:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.13);
  background: #f7fafd;
}
</style>
