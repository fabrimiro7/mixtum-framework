/**
 * Extracts YouTube video ID from watch, Shorts, youtu.be or embed URLs
 * and returns the embed URL, or null if invalid.
 */
export function youtubeLinkToEmbedUrl(link: string | null | undefined): string | null {
  if (!link || typeof link !== 'string') {
    return null;
  }
  const trimmed = link.trim();
  if (!trimmed) {
    return null;
  }

  let videoId: string | null = null;

  // Already embed: https://www.youtube.com/embed/VIDEO_ID
  const embedMatch = trimmed.match(/youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/i);
  if (embedMatch) {
    videoId = embedMatch[1];
  }

  // Watch: https://www.youtube.com/watch?v=VIDEO_ID
  if (!videoId) {
    const watchMatch = trimmed.match(/youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/i);
    if (watchMatch) {
      videoId = watchMatch[1];
    }
  }

  // Shorts: https://www.youtube.com/shorts/VIDEO_ID
  if (!videoId) {
    const shortsMatch = trimmed.match(/youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})/i);
    if (shortsMatch) {
      videoId = shortsMatch[1];
    }
  }

  // youtu.be: https://youtu.be/VIDEO_ID
  if (!videoId) {
    const beMatch = trimmed.match(/youtu\.be\/([a-zA-Z0-9_-]{11})/i);
    if (beMatch) {
      videoId = beMatch[1];
    }
  }

  if (!videoId) {
    return null;
  }

  return `https://www.youtube.com/embed/${videoId}`;
}
