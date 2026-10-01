export async function fetchMeetings() {
  const response = await fetch("/api/meetings", { cache: "no-store" })
  if (!response.ok) {
    throw new Error("Could not load meetings")
  }
  const body = await response.json()
  return body.meetings
}
