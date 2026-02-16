/**
 * Converts plain URLs and Markdown-style links in text to HTML anchors.
 * Protects existing <a> tags from being double-processed.
 */
export function convertUrlsToLinks(text: string): string {
  const mdLinkPattern = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/gi;
  const urlPattern = /((https?:\/\/|www\.)[^\s<>"']+)/gi;
  const placeholderPrefix = '@@MD_LINK_';
  const anchorPlaceholderPrefix = '@@ANCHOR_';
  const placeholders: string[] = [];
  const anchorPlaceholders: string[] = [];

  // 1. Ripara frammenti di anchor corrotti (es. "url" target="_blank" rel="noopener noreferrer">url)
  let converted = text.replace(
    /"(https?:\/\/[^"]+)"\s+target="_blank"\s+rel=["']noopener\s+noreferrer["']\s*>\s*\1/gi,
    (_match, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
  );

  // 2. Proteggi i tag <a href="...">...</a> esistenti (es. da rich-text-editor) per evitare
  //    che convertUrlsToLinks sostituisca gli URL dentro href="..." creando HTML invalido
  converted = converted.replace(
    /<a\s+[^>]*href=["'](https?:\/\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi,
    (_match: string) => {
      const placeholder = `${anchorPlaceholderPrefix}${anchorPlaceholders.length}@@`;
      anchorPlaceholders.push(_match);
      return placeholder;
    }
  );

  // 3. Converti link in formato Markdown [testo](url)
  converted = converted.replace(mdLinkPattern, (_match: string, label: string, url: string) => {
    const anchor = `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    const placeholder = `${placeholderPrefix}${placeholders.length}@@`;
    placeholders.push(anchor);
    return placeholder;
  });

  // 4. Converti URL "nudi" in link (solo nel testo, non dentro attributi)
  converted = converted.replace(urlPattern, (match: string) => {
    const href = match.toLowerCase().startsWith('http') ? match : `http://${match}`;
    return `<a href="${href}" target="_blank" rel="noopener noreferrer">${match}</a>`;
  });

  // 5. Ripristina placeholder dei link Markdown
  placeholders.forEach((anchor, index) => {
    converted = converted.replace(`${placeholderPrefix}${index}@@`, anchor);
  });

  // 6. Ripristina i tag <a> originali protetti
  anchorPlaceholders.forEach((anchor, index) => {
    converted = converted.replace(`${anchorPlaceholderPrefix}${index}@@`, anchor);
  });

  return converted;
}
