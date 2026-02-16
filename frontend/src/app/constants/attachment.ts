import { environment } from 'src/environments/django';

export const MAX_ATTACHMENT_SIZE_MB = environment.attachmentMaxSizeMb ?? 5;
export const MAX_ATTACHMENT_SIZE_BYTES = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024;

/**
 * Format a byte count into a human-readable megabyte string with two decimals.
 */
export function formatBytesToMb(bytes: number): string {
  return (bytes / (1024 * 1024)).toFixed(2);
}
