import { NotionBlock, NotionBlockType } from './notion-block.model';

export function inferBlockTypeFromHtml(html: string): NotionBlockType {
  const trimmed = (html || '').trim().toLowerCase();
  if (trimmed.startsWith('<h1')) return 'heading1';
  if (trimmed.startsWith('<h2')) return 'heading2';
  if (trimmed.startsWith('<blockquote')) return 'quote';
  if (trimmed.startsWith('<ul')) return 'bulleted';
  if (trimmed.startsWith('<ol')) return 'numbered';
  if (trimmed.startsWith('<hr')) return 'divider';
  if (trimmed.startsWith('<p')) return 'paragraph';
  return 'paragraph';
}

export function extractEditableContent(html: string, type: NotionBlockType): string {
  if (!html) return '';
  if (type === 'divider') return '';
  if (type === 'bulleted' || type === 'numbered') {
    const items = Array.from(html.matchAll(/<li[^>]*>(.*?)<\/li>/gi)).map(match => match[1]);
    const cleaned = items.map(stripTags).map(s => s.trim()).filter(Boolean);
    return cleaned.join('\n');
  }
  const tagMatch = html.match(/<(p|h1|h2|blockquote)[^>]*>([\s\S]*?)<\/(p|h1|h2|blockquote)>/i);
  if (tagMatch && tagMatch[2] !== undefined) {
    return tagMatch[2].trim();
  }
  return html.trim();
}

export function serializeBlockToHtml(block: NotionBlock): string {
  const content = (block.content || '').trim();
  switch (block.type) {
    case 'heading1':
      return `<h1>${content}</h1>`;
    case 'heading2':
      return `<h2>${content}</h2>`;
    case 'quote':
      return `<blockquote>${content}</blockquote>`;
    case 'bulleted': {
      const items = splitLines(content);
      const li = items.map(item => `<li>${item}</li>`).join('');
      return `<ul>${li}</ul>`;
    }
    case 'numbered': {
      const items = splitLines(content);
      const li = items.map(item => `<li>${item}</li>`).join('');
      return `<ol>${li}</ol>`;
    }
    case 'divider':
      return '<hr />';
    case 'paragraph':
    default:
      return `<p>${content}</p>`;
  }
}

export function blockTitleFromContent(block: NotionBlock): string {
  if (block.type === 'divider') {
    return 'Divider';
  }
  const raw = block.content || '';
  const text = stripTags(raw).replace(/\s+/g, ' ').trim();
  if (!text) {
    return block.type === 'paragraph' ? 'Testo' : 'Blocco';
  }
  return text.length > 40 ? `${text.slice(0, 40)}...` : text;
}

function splitLines(text: string): string[] {
  return text
    .replace(/<br\s*\/?>/gi, '\n')
    .split(/\n+/)
    .map(line => line.trim())
    .filter(Boolean);
}

function stripTags(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}
