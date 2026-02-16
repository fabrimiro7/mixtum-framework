export type BrandingColors = Record<string, string>;

export interface BrandingSettings {
  id?: number;
  workspace?: number | null;
  colors?: BrandingColors;
  logo_full?: string | null;
  logo_compact?: string | null;
  favicon?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface BrandingEffective {
  workspace_id?: number | null;
  colors: BrandingColors;
  logo_full?: string | null;
  logo_compact?: string | null;
  favicon?: string | null;
}
