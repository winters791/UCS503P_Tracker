const DAY_START_MINUTES = 8 * 60; // grid starts at 08:00
const BLOCK_MINUTES = 50;
const BUFFER_MINUTES = 10;
const SLOT_MINUTES = BLOCK_MINUTES + BUFFER_MINUTES;

function formatMinutes(totalMinutes: number): string {
  const hours24 = Math.floor(totalMinutes / 60) % 24;
  const minutes = totalMinutes % 60;
  const period = hours24 >= 12 ? "PM" : "AM";
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  return `${hours12}:${minutes.toString().padStart(2, "0")} ${period}`;
}

export function slotLabel(slotIndex: number): { start: string; end: string } {
  const start = DAY_START_MINUTES + slotIndex * SLOT_MINUTES;
  const end = start + BLOCK_MINUTES;
  return { start: formatMinutes(start), end: formatMinutes(end) };
}

export function bufferLabel(slotIndex: number): string {
  const bufferStart = DAY_START_MINUTES + slotIndex * SLOT_MINUTES + BLOCK_MINUTES;
  return `${formatMinutes(bufferStart)} buffer`;
}

export function cellKey(day: string, slotIndex: number): string {
  return `${day}::${slotIndex}`;
}
