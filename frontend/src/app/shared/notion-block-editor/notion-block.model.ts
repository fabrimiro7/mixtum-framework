export type NotionBlockType =
  | 'paragraph'
  | 'heading1'
  | 'heading2'
  | 'bulleted'
  | 'numbered'
  | 'quote'
  | 'divider';

export interface NotionBlock {
  id?: number | null;
  type: NotionBlockType;
  content: string;
  title?: string;
  position?: number;
}

export const NOTION_BLOCK_TYPES: Array<{ type: NotionBlockType; label: string }> = [
  { type: 'paragraph', label: 'Testo' },
  { type: 'heading1', label: 'Titolo 1' },
  { type: 'heading2', label: 'Titolo 2' },
  { type: 'bulleted', label: 'Lista puntata' },
  { type: 'numbered', label: 'Lista numerata' },
  { type: 'quote', label: 'Citazione' },
  { type: 'divider', label: 'Separatore' },
];
