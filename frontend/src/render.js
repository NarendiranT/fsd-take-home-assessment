import {
  attendees,
  clientName,
  conflictFields,
  formatWhen,
  isVirtual,
  pageWindow,
  shown,
  titleName,
  visibleMeetings,
  whenText,
} from "./format.js"
import { select, setConflict, setConflictOpen, setPage, setQuery, setSource, show } from "./store.js"

const ICONS = {
  logo: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 10h18"/></svg>`,
  search: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>`,
  pin: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.2"/></svg>`,
  video: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="14" height="12" rx="2"/><path d="M16 10l6-3v10l-6-3z"/></svg>`,
  calendar: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M8 2v4M16 2v4M3 10h18"/></svg>`,
  user: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="3.2"/><path d="M5 19c1.5-3 3.8-4.5 7-4.5S17.5 16 19 19"/></svg>`,
  users: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="9" cy="8" r="3"/><path d="M3 19c1.2-2.6 3-4 6-4s4.8 1.4 6 4"/><circle cx="17" cy="9" r="2.2"/><path d="M16 15c2 .3 3.5 1.4 4.5 4"/></svg>`,
  alert: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l10 18H2L12 3z"/><path d="M12 10v4M12 17h.01"/></svg>`,
  check: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/></svg>`,
  chevron: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>`,
  chevronUp: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 14l6-6 6 6"/></svg>`,
  chevronDown: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 10l6 6 6-6"/></svg>`,
  list: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13"/><path d="M4 6h.01M4 12h.01M4 18h.01"/></svg>`,
  link: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/></svg>`,
}

export function draw(root, state) {
  if (state.status === "loading") {
    root.replaceChildren(el("p", "message", "Loading meetings…"))
    return
  }
  if (state.status === "failed") {
    root.replaceChildren(el("p", "message", state.error || "Could not load meetings"))
    return
  }

  const typing = document.activeElement?.id === "q"
  const caret = typing ? document.activeElement.selectionStart : null
  const scrollY = window.scrollY

  const page = el("div", "app")
  page.append(header(state))
  page.append(state.view === "about" ? about() : workspace(state))
  root.replaceChildren(page)
  window.scrollTo(0, scrollY)

  if (!typing) return
  const input = page.querySelector("#q")
  input.focus()
  const pos = caret ?? input.value.length
  input.setSelectionRange(pos, pos)
}

function header(state) {
  const bar = el("header", "top")
  const brand = el("div", "brand")
  const logo = el("span", "logo")
  logo.append(icon("logo"))
  brand.append(logo, el("span", null, "Event Sync Service"))
  const nav = el("nav", "nav")
  nav.append(navButton("Meetings", "meetings", state.view), navButton("About", "about", state.view))
  bar.append(brand, nav, el("p", "tagline", "Reconciled view of CRM and Calendar events"))
  return bar
}

function navButton(label, view, current) {
  const button = el("button", null, label)
  button.type = "button"
  if (current === view) button.setAttribute("aria-current", "page")
  button.addEventListener("click", () => show(view))
  return button
}

function about() {
  const section = el("section", "about")
  section.append(
    el("h1", null, "About"),
    el(
      "p",
      null,
      "Event Sync Service shows one list of sales meetings from the CRM and the calendar. A meeting in both systems keeps both values. Where the place, the time, or a cancellation disagrees, the meeting is marked. Neither source is treated as the truth.",
    ),
  )
  return section
}

function workspace(state) {
  const rows = visibleMeetings(state.meetings, state)
  const span = pageWindow(rows.length, state.page)
  const pageRows = rows.slice(span.start, span.end)
  const selected = rows.find((meeting) => meeting.id === state.selectedId) || rows[0] || null
  const section = el("div", "workspace")
  const main = el("section", "list-pane")
  main.append(el("h1", null, "Meetings"))
  main.append(
    el(
      "p",
      "lede",
      "Unified view of meetings from CRM and Calendar with source information and conflicts.",
    ),
  )
  main.append(toolbar(state, rows.length))
  main.append(table(pageRows, selected))
  if (rows.length) main.append(pager(span, rows.length))
  section.append(main, detailPane(selected, state))
  return section
}

function toolbar(state, count) {
  const bar = el("div", "toolbar")
  const search = el("label", "search-wrap")
  search.append(icon("search"))
  const input = document.createElement("input")
  input.id = "q"
  input.className = "search"
  input.type = "search"
  input.placeholder = "Search by client, title, attendee..."
  input.setAttribute("aria-label", "Search by client, title, or attendee")
  input.value = state.query
  input.addEventListener("input", () => setQuery(input.value))
  search.append(input)

  bar.append(
    search,
    filterSelect("Source", state.source, setSource, [
      ["all", "All Sources"],
      ["crm", "CRM"],
      ["calendar", "Calendar"],
    ]),
    filterSelect("Status", state.conflict, setConflict, [
      ["all", "All Statuses"],
      ["conflicts", "Has conflicts"],
      ["clear", "No conflicts"],
    ]),
    el("p", "count", `${count} meeting${count === 1 ? "" : "s"}`),
  )
  return bar
}

function pager(span, total) {
  const bar = el("nav", "pager")
  bar.setAttribute("aria-label", "Pagination")
  bar.append(pageButton("Previous", span.current - 1, span.current === 0))
  for (let index = 0; index < span.pages; index++) {
    const button = pageButton(String(index + 1), index, false)
    if (index === span.current) button.setAttribute("aria-current", "page")
    bar.append(button)
  }
  bar.append(pageButton("Next", span.current + 1, span.current >= span.pages - 1))
  bar.append(el("span", "pager-range", `${span.start + 1}–${span.end} of ${total}`))
  return bar
}

function pageButton(label, page, disabled) {
  const button = el("button", "page-btn", label)
  button.type = "button"
  button.disabled = disabled
  if (!disabled) button.addEventListener("click", () => setPage(page))
  return button
}

function filterSelect(label, value, onChange, options) {
  const select = document.createElement("select")
  select.className = "filter"
  select.setAttribute("aria-label", label)
  for (const [optionValue, text] of options) {
    const option = el("option", null, text)
    option.value = optionValue
    select.append(option)
  }
  select.value = value
  select.addEventListener("change", () => onChange(select.value))
  return select
}

function table(rows, selected) {
  const wrap = el("div", "table-card")
  const tableEl = document.createElement("table")
  tableEl.className = "meetings"
  const head = document.createElement("thead")
  const headRow = document.createElement("tr")
  for (const label of ["Client / Title", "Date & Time", "Owner", "Location", "Sources", "Status", ""]) {
    headRow.append(el("th", null, label))
  }
  head.append(headRow)
  const body = document.createElement("tbody")
  if (!rows.length) {
    const row = document.createElement("tr")
    const cell = el("td", "empty", "No meetings match.")
    cell.colSpan = 7
    row.append(cell)
    body.append(row)
  }
  for (const meeting of rows) body.append(meetingRow(meeting, selected && meeting.id === selected.id))
  tableEl.append(head, body)
  wrap.append(tableEl)
  return wrap
}

function meetingRow(meeting, isSelected) {
  const name = clientName(meeting) || "—"
  const title = titleName(meeting)
  const row = document.createElement("tr")
  row.tabIndex = 0
  row.setAttribute("aria-selected", isSelected ? "true" : "false")
  row.setAttribute("aria-label", title && title !== name ? `${name}, ${title}` : name)
  const choose = () => select(meeting.id)
  row.addEventListener("click", choose)
  row.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return
    event.preventDefault()
    choose()
  })

  const client = el("td")
  client.append(el("span", "primary", name))
  if (title && title !== name) client.append(el("span", "secondary", title))

  const when = listWhen(meeting.when)
  const whenCell = el("td", "when")
  whenCell.append(el("span", "primary", when.date))
  if (when.time) whenCell.append(el("span", "secondary", when.time))

  const location = shown(meeting.location)
  const place = el("td", "loc-cell")
  const placeLine = el("span", "loc")
  if (location) {
    placeLine.title = location
    placeLine.append(locIcon(location))
  }
  placeLine.append(el("span", null, location || "—"))
  place.append(placeLine)

  const sources = el("td", "sources")
  for (const name of sourceNames(meeting.source)) sources.append(chip(name))

  const status = el("td")
  status.append(statusPill(meeting.conflict_count))
  const more = el("td", "more")
  more.append(icon("chevron"))
  row.append(client, whenCell, el("td", null, "—"), place, sources, status, more)
  return row
}

function detailPane(meeting, state) {
  const aside = el("aside", "detail-pane")
  aside.append(meeting ? detail(meeting, state) : el("p", "empty-card", "No meetings match."))
  return aside
}

function detail(meeting, state) {
  const card = el("article", "detail")
  const head = el("div", "detail-head")
  const titles = el("div")
  const name = clientName(meeting) || "—"
  const title = titleName(meeting)
  titles.append(el("h2", null, name))
  if (title && title !== name) titles.append(el("p", "subtitle", title))
  head.append(titles)
  if (meeting.conflict_count) head.append(statusPill(meeting.conflict_count))
  card.append(head)

  card.append(meta("calendar", whenLine(meeting.when)))
  card.append(meta("user", "Owner: —"))
  const place = shown(meeting.location) || "—"
  card.append(meta(isVirtual(place) ? "video" : "pin", `Location: ${place}`))
  const sources = el("div", "meta")
  sources.append(icon("link"), el("span", null, "Sources:"))
  for (const name of sourceNames(meeting.source)) sources.append(chip(name))
  card.append(sources)

  card.append(sectionLabel("users", "Attendees"))
  const people = attendees(meeting)
  if (!people.length) card.append(el("p", "muted", "None"))
  else {
    const chips = el("div", "chips")
    for (const person of people) chips.append(el("span", "chip", person))
    card.append(chips)
  }

  const fields = conflictFields(meeting)
  const label = sectionLabel("alert", "Conflicts")
  label.classList.add("danger")
  card.append(label)
  if (!fields.length) card.append(el("p", "muted", "No conflicts between sources."))
  const current = openKey(fields, state)
  for (const field of fields) card.append(conflictCard(field, field.key === current))

  card.append(sectionLabel("list", "Field Details"))
  card.append(fieldTable(meeting))
  return card
}

function conflictCard(field, open) {
  const card = el("div", "conflict-card")
  const button = document.createElement("button")
  button.type = "button"
  button.className = "conflict-toggle"
  button.setAttribute("aria-expanded", open ? "true" : "false")
  button.append(el("span", null, field.label), icon(open ? "chevronUp" : "chevronDown"))
  button.addEventListener("click", () => setConflictOpen(open ? "" : field.key))
  card.append(button)
  if (!open) return card
  const body = el("div", "conflict-body")
  body.append(sourceLine("CRM", field.key === "when" ? whenText(field.crm) : field.crm))
  body.append(sourceLine("Calendar", field.key === "when" ? whenText(field.calendar) : field.calendar))
  body.append(el("p", "conflict-note", field.note))
  card.append(body)
  return card
}

function sourceLine(name, value) {
  const line = el("div", "source-line")
  line.append(chip(name), el("span", null, value || "—"))
  return line
}

function fieldTable(meeting) {
  const tableEl = document.createElement("table")
  tableEl.className = "fields"
  const head = document.createElement("tr")
  for (const label of ["Field", "CRM", "Calendar", "Final"]) head.append(el("th", null, label))
  tableEl.append(head)
  const whenFinal = meeting.when.conflict
    ? [whenText(meeting.when.crm), whenText(meeting.when.calendar)].filter(Boolean).join(" / ")
    : whenText(shown(meeting.when))
  const rows = [
    ["Client", meeting.who.crm, meeting.who.calendar, shown(meeting.who)],
    ["Title", meeting.title.crm, meeting.title.calendar, shown(meeting.title)],
    ["Date & Time", whenText(meeting.when.crm), whenText(meeting.when.calendar), whenFinal],
    ["Location", meeting.location.crm, meeting.location.calendar, shown(meeting.location)],
    ["Owner", "", "", ""],
  ]
  for (const [label, crm, calendar, final] of rows) {
    const row = document.createElement("tr")
    row.append(el("td", null, label), el("td", null, crm || "—"), el("td", null, calendar || "—"), el("td", null, final || "—"))
    tableEl.append(row)
  }
  const wrap = el("div", "fields-wrap")
  wrap.append(tableEl)
  return wrap
}

function listWhen(field) {
  if (field.conflict) {
    const date = [whenText(field.crm), whenText(field.calendar)].filter(Boolean).join(" / ")
    return { date: date || "—", time: "" }
  }
  return formatWhen(shown(field)) || { date: "—", time: "" }
}

function whenLine(field) {
  if (field.conflict) {
    return [whenText(field.crm), whenText(field.calendar)].filter(Boolean).join(" / ") || "—"
  }
  return whenText(shown(field)) || "—"
}

function openKey(fields, state) {
  if (!fields.length) return null
  if (state.openConflict === "") return null
  if (fields.some((field) => field.key === state.openConflict)) return state.openConflict
  return fields[0].key
}

function sourceNames(source) {
  if (source === "crm") return ["CRM"]
  if (source === "calendar") return ["Calendar"]
  return ["CRM", "Calendar"]
}

function statusPill(count) {
  const kind = !count ? "ok" : count > 1 ? "bad" : "warn"
  const pill = el("span", `pill ${kind}`)
  const label = count === 1 ? "1 conflict" : count ? `${count} conflicts` : "No conflicts"
  pill.append(icon(count ? "alert" : "check"), document.createTextNode(label))
  return pill
}

function chip(name) {
  return el("span", `pill ${name.toLowerCase()}`, name)
}

function locIcon(text) {
  const node = icon(isVirtual(text) ? "video" : "pin")
  node.classList.add(isVirtual(text) ? "video" : "pin")
  return node
}

function meta(name, text) {
  const row = el("div", "meta")
  const mark = icon(name)
  if (name === "video" || name === "pin") mark.classList.add(name)
  row.append(mark, el("span", null, text))
  return row
}

function sectionLabel(name, text) {
  const row = el("div", "section-label")
  row.append(icon(name), el("span", null, text))
  return row
}

function icon(name) {
  const node = el("span", "icon")
  node.innerHTML = ICONS[name]
  return node
}

function el(tag, className, text) {
  const node = document.createElement(tag)
  if (className) node.className = className
  if (text != null) node.textContent = text
  return node
}
