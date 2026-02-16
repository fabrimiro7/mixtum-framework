export interface DocumentType {
  id: number;
  code: string;
  title: string;
  description?: string;
  default_template?: number | null;
  requires_signature?: boolean;
  is_active?: boolean;
  sort_order?: number;
}

export interface DocumentStatus {
  id: number;
  code: string;
  title: string;
  is_terminal?: boolean;
  sort_order?: number;
}

export interface DocumentCategory {
  id: number;
  slug: string;
  title: string;
  parent?: number | null;
  color?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface Block {
  id: number;
  title: string;
  content: string;
  is_active?: boolean;
}

export interface DocumentTemplateBlock {
  id: number;
  block: number;
  block_title?: string;
  title_snapshot: string;
  content_snapshot: string;
  position: number;
}

export interface DocumentTemplate {
  id: number;
  title: string;
  description?: string;
  template_blocks?: DocumentTemplateBlock[];
}

export interface DocumentBlock {
  id: number;
  source_template_block?: number | null;
  title: string;
  content: string;
  position: number;
}

export interface DocumentCategoryAssignment {
  id: number;
  category: number;
  category_title?: string;
  is_primary?: boolean;
}

export interface Document {
  id: number;
  title: string;
  status: number;
  type: number;
  template?: number | null;
  categories?: number[];
  category_assignments?: DocumentCategoryAssignment[];
  context_snapshot?: Record<string, unknown>;
  signers_snapshot?: any[];
  rendered_html?: string | null;
  render_hash?: string | null;
  frozen_at?: string | null;
  is_editable?: boolean;
  blocks?: DocumentBlock[];
  created_at?: string;
  updated_at?: string;
}
