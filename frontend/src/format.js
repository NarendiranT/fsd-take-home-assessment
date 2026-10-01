const CONFLICTS = [
  ["title", "Title", "Different title values between sources."],
  ["when", "Date & Time", "Different time values between sources."],
  ["who", "Client", "Different client values between sources."],
  ["location", "Location", "Different location values between sources."],
  ["status", "Status", "Different status values between sources."],
  ["notes", "Notes", "Different note values between sources."],
  ["ids", "Ids", "Different id values between sources."],
]

export function formatWhen(text) {
  if (!text) return null
  const match = /^(\d{1,2}) ([A-Za-z]{3}) (\d{4})(?:, (\d{2}):(\d{2}))?$/.exec(text)
  if (!match) return { date: text, time: "" }
  const date = `${match[2]} ${Number(match[1])}, ${match[3]}`
  if (!match[4]) return { date, time: "" }
  let hour = Number(match[4])
  const suffix = hour >= 12 ? "PM" : "AM"
  hour = hour % 12 || 12
  return { date, time: `${hour}:${match[5]} ${suffix}` }
}

export function whenText(text) {
  const formatted = formatWhen(text)
  if (!formatted) return ""
  return formatted.time ? `${formatted.date}, ${formatted.time}` : formatted.date
}

export function shown(field) {
  if (!field?.crm && !field?.calendar) return ""
  if (field.conflict) return [field.crm, field.calendar].filter(Boolean).join(" / ")
  if (field.crm && field.calendar) {
    return field.crm.length >= field.calendar.length ? field.crm : field.calendar
  }
  return field.crm || field.calendar
}

export function clientName(meeting) {
  const who = meeting.who?.crm
  if (who) {
    const comma = who.indexOf(", ")
    return comma >= 0 ? who.slice(comma + 2) : who
  }
  return meeting.title?.calendar || meeting.title?.crm || ""
}

export function titleName(meeting) {
  return meeting.title?.crm || meeting.title?.calendar || ""
}

export function attendees(meeting) {
  if (!meeting.who?.calendar) return []
  return meeting.who.calendar.split(",").map((part) => part.trim()).filter(Boolean)
}

export function isVirtual(text) {
  return /zoom|teams|virtual|meet/i.test(text || "")
}

export function conflictFields(meeting) {
  return CONFLICTS.filter(([key]) => meeting[key]?.conflict).map(([key, label, note]) => ({
    key,
    label,
    note,
    crm: meeting[key].crm,
    calendar: meeting[key].calendar,
  }))
}

export const PAGE_SIZE = 8

export function pageWindow(total, page, size = PAGE_SIZE) {
  const pages = Math.max(1, Math.ceil(total / size) || 1)
  const current = Math.min(Math.max(page, 0), pages - 1)
  const start = total === 0 ? 0 : current * size
  const end = Math.min(start + size, total)
  return { current, pages, start, end }
}

export function visibleMeetings(meetings, filters) {
  const query = filters.query.trim().toLowerCase()
  return meetings.filter((meeting) => {
    if (filters.source === "crm" && meeting.source === "calendar") return false
    if (filters.source === "calendar" && meeting.source === "crm") return false
    if (filters.conflict === "conflicts" && !meeting.conflict_count) return false
    if (filters.conflict === "clear" && meeting.conflict_count) return false
    if (!query) return true
    const haystack = [
      clientName(meeting),
      titleName(meeting),
      meeting.who?.crm,
      meeting.who?.calendar,
      meeting.title?.crm,
      meeting.title?.calendar,
    ]
    return haystack.filter(Boolean).join(" ").toLowerCase().includes(query)
  })
}

function demo() {
  const when = formatWhen("10 Mar 2025, 14:00")
  if (when.date !== "Mar 10, 2025" || when.time !== "2:00 PM") throw new Error("afternoon")
  if (formatWhen("10 Mar 2025, 00:00").time !== "12:00 AM") throw new Error("midnight")
  if (formatWhen("10 Mar 2025, 12:00").time !== "12:00 PM") throw new Error("noon")
  if (formatWhen("15 Mar 2025").time !== "" || formatWhen("15 Mar 2025").date !== "Mar 15, 2025") {
    throw new Error("date only")
  }

  const meeting = {
    source: "both",
    conflict_count: 2,
    title: { crm: "Q1 Portfolio Review", calendar: "Q1 Portfolio Review - Meridian Capital", conflict: false },
    who: { crm: "David Park, Meridian Capital", calendar: "Sarah Chen, David Park", conflict: false },
    when: { crm: "10 Mar 2025, 14:00", calendar: "10 Mar 2025, 15:00", conflict: true },
    location: { crm: "HQ - Conference Room B", calendar: "Zoom", conflict: true },
    status: { crm: "Completed", calendar: "confirmed", conflict: false },
    notes: { crm: null, calendar: null, conflict: false },
    ids: { crm: "CRM-1001", calendar: "CAL-A1", conflict: false },
  }
  if (clientName(meeting) !== "Meridian Capital") throw new Error("client")
  if (titleName(meeting) !== "Q1 Portfolio Review") throw new Error("title")
  if (attendees(meeting).join("|") !== "Sarah Chen|David Park") throw new Error("attendees")
  if (shown(meeting.location) !== "HQ - Conference Room B / Zoom") throw new Error("conflict join")
  if (shown(meeting.title) !== "Q1 Portfolio Review - Meridian Capital") throw new Error("longer title")
  if (shown({ crm: "Boston Office", calendar: "Boston Office - Room 301", conflict: false }) !== "Boston Office - Room 301") {
    throw new Error("longer place")
  }
  if (conflictFields(meeting).map((field) => field.key).join() !== "when,location") throw new Error("conflicts")

  const calendarOnly = {
    ...meeting,
    source: "calendar",
    conflict_count: 0,
    who: { crm: null, calendar: "Sarah Chen", conflict: false },
    title: { crm: null, calendar: "Weekly Team Sync", conflict: false },
  }
  if (clientName(calendarOnly) !== "Weekly Team Sync") throw new Error("calendar client")
  if (visibleMeetings([meeting], { query: "david park", source: "all", conflict: "all" }).length !== 1) {
    throw new Error("search")
  }
  if (visibleMeetings([meeting, calendarOnly], { query: "", source: "crm", conflict: "all" }).length !== 1) {
    throw new Error("crm filter")
  }
  if (visibleMeetings([meeting], { query: "", source: "all", conflict: "clear" }).length !== 0) {
    throw new Error("clear filter")
  }
  const window = pageWindow(24, 5)
  if (window.current !== 2 || window.start !== 16 || window.end !== 24 || window.pages !== 3) {
    throw new Error("page")
  }
  if (pageWindow(0, 3).end !== 0 || pageWindow(8, 0).pages !== 1) throw new Error("page edges")
}

if (typeof process !== "undefined" && process.argv[1]?.endsWith("format.js")) demo()
