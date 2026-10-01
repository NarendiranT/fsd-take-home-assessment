import { fetchMeetings } from "./api.js"

const listeners = new Set()

const state = {
  meetings: [],
  status: "loading",
  error: null,
  selectedId: null,
  query: "",
  source: "all",
  conflict: "all",
  view: "meetings",
  openConflict: null,
  page: 0,
}

export function subscribe(listener) {
  listeners.add(listener)
}

function emit() {
  for (const listener of listeners) listener(state)
}

export async function load(quiet = false) {
  if (!quiet) {
    state.status = "loading"
    state.error = null
    emit()
  }
  try {
    state.meetings = await fetchMeetings()
    state.status = "ready"
    state.error = null
    const stillThere = state.meetings.some((meeting) => meeting.id === state.selectedId)
    if (!stillThere) state.selectedId = state.meetings[0]?.id ?? null
  } catch (error) {
    if (quiet) return
    state.meetings = []
    state.status = "failed"
    state.error = error.message
  }
  emit()
}

export function watch() {
  const source = new EventSource("/api/events")
  let opened = false
  source.onopen = () => {
    if (!opened) {
      opened = true
      return
    }
    load(true)
  }
  source.onmessage = () => load(true)
}

export function select(id) {
  state.selectedId = id
  state.openConflict = null
  emit()
}

export function setQuery(query) {
  state.query = query
  state.page = 0
  emit()
}

export function setSource(source) {
  state.source = source
  state.page = 0
  emit()
}

export function setConflict(conflict) {
  state.conflict = conflict
  state.page = 0
  emit()
}

export function setPage(page) {
  state.page = page
  emit()
}

export function show(view) {
  state.view = view
  emit()
}

export function setConflictOpen(key) {
  state.openConflict = key
  emit()
}
