import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely — use this everywhere */
// this is a test
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
