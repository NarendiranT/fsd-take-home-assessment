export async function fetchMeetings() {
  const response = await fetch("/api/meetings")
  if (!response.ok) {
    throw new Error("Could not load meetings")
  }
  const body = await response.json()
  return body.meetings
}
