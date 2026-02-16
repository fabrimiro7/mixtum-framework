import { Component, OnInit } from '@angular/core';
import { CookieService } from 'ngx-cookie-service';
import { BrandingService } from 'src/app/services/theme/branding.service';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';
import { BRANDING_COLOR_KEYS } from 'src/app/constants/branding';
import { BrandingEffective } from 'src/app/models/branding';
import { Workspace } from 'src/app/models/workspace';
import { PermissionService } from 'src/app/services/auth/permission.service';

@Component({
  selector: 'app-customizer',
  templateUrl: './customizer.component.html',
  styleUrls: ['./customizer.component.css']
})
export class CustomizerComponent implements OnInit {
  colorKeys = BRANDING_COLOR_KEYS;

  isSuperAdmin = false;

  workspaces: Workspace[] = [];
  selectedWorkspaceId: number | null = null;

  effectiveColors: Record<string, string> = {};

  globalColors: Record<string, string> = {};
  workspaceColors: Record<string, string> = {};
  clearedWorkspaceKeys = new Set<string>();

  globalLogoUrls: Record<string, string | null> = {
    logo_full: null,
    logo_compact: null,
    favicon: null,
  };

  workspaceLogoUrls: Record<string, string | null> = {
    logo_full: null,
    logo_compact: null,
    favicon: null,
  };

  logoFiles: Record<'global' | 'workspace', Record<string, File | null>> = {
    global: { logo_full: null, logo_compact: null, favicon: null },
    workspace: { logo_full: null, logo_compact: null, favicon: null },
  };

  logoPreviews: Record<'global' | 'workspace', Record<string, string | null>> = {
    global: { logo_full: null, logo_compact: null, favicon: null },
    workspace: { logo_full: null, logo_compact: null, favicon: null },
  };

  constructor(
    private brandingService: BrandingService,
    private workspaceService: WorkspaceService,
    private cookieService: CookieService,
    private permissionService: PermissionService,
  ) {}

  ngOnInit(): void {
    const token = this.cookieService.get('token');
    try {
      this.isSuperAdmin = this.permissionService.checkPermission(token) === 'SuperAdmin';
    } catch {
      this.isSuperAdmin = false;
    }

    this.brandingService.branding$.subscribe((branding: BrandingEffective | null) => {
      this.effectiveColors = branding?.colors || {};
    });

    this.loadGlobal();
    this.loadWorkspaces();
  }

  loadGlobal(): void {
    this.brandingService.getGlobal().subscribe((data) => {
      this.globalColors = data.colors || {};
      this.globalLogoUrls['logo_full'] = data.logo_full || null;
      this.globalLogoUrls['logo_compact'] = data.logo_compact || null;
      this.globalLogoUrls['favicon'] = data.favicon || null;
      this.logoFiles.global = { logo_full: null, logo_compact: null, favicon: null };
      this.logoPreviews.global = { logo_full: null, logo_compact: null, favicon: null };
    });
  }

  loadWorkspaces(): void {
    this.workspaceService.listWorkspaces().subscribe((data) => {
      this.workspaces = data || [];
      if (this.workspaces.length > 0) {
        const activeId = this.workspaceService.getActiveWorkspaceId();
        const hasActive = activeId && this.workspaces.some((ws) => ws.id === activeId);
        this.selectedWorkspaceId = hasActive ? activeId : this.workspaces[0].id;
        this.loadWorkspace(this.selectedWorkspaceId as number);
      }
    });
  }

  loadWorkspace(workspaceId: number): void {
    this.brandingService.getWorkspace(workspaceId).subscribe((data) => {
      this.workspaceColors = data.colors || {};
      this.clearedWorkspaceKeys.clear();
      this.workspaceLogoUrls['logo_full'] = data.logo_full || null;
      this.workspaceLogoUrls['logo_compact'] = data.logo_compact || null;
      this.workspaceLogoUrls['favicon'] = data.favicon || null;
      this.logoFiles.workspace = { logo_full: null, logo_compact: null, favicon: null };
      this.logoPreviews.workspace = { logo_full: null, logo_compact: null, favicon: null };
    });
  }

  onWorkspaceSelect(workspaceId: number): void {
    this.selectedWorkspaceId = workspaceId;
    this.loadWorkspace(workspaceId);
  }

  onGlobalColorText(key: string, value: string): void {
    this.globalColors[key] = value;
  }

  onGlobalColorInput(key: string, value: string): void {
    this.globalColors[key] = value;
  }

  onWorkspaceColorText(key: string, value: string): void {
    this.workspaceColors[key] = value;
    this.clearedWorkspaceKeys.delete(key);
  }

  onWorkspaceColorInput(key: string, value: string): void {
    this.workspaceColors[key] = value;
    this.clearedWorkspaceKeys.delete(key);
  }

  resetWorkspaceColor(key: string): void {
    delete this.workspaceColors[key];
    this.clearedWorkspaceKeys.add(key);
  }

  onLogoFileChange(scope: 'global' | 'workspace', key: 'logo_full' | 'logo_compact' | 'favicon', event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files && input.files.length ? input.files[0] : null;
    this.logoFiles[scope][key] = file;
    if (file) {
      this.logoPreviews[scope][key] = URL.createObjectURL(file);
    }
  }

  getLogoDisplay(scope: 'global' | 'workspace', key: 'logo_full' | 'logo_compact' | 'favicon'): string | null {
    return this.logoPreviews[scope][key] || this.getLogoUrl(scope, key);
  }

  getLogoUrl(scope: 'global' | 'workspace', key: 'logo_full' | 'logo_compact' | 'favicon'): string | null {
    if (scope === 'global') {
      return this.globalLogoUrls[key] || null;
    }
    return this.workspaceLogoUrls[key] || null;
  }

  saveGlobal(): void {
    if (!this.isSuperAdmin) {
      return;
    }
    const payload = new FormData();
    const colorsPayload: Record<string, string | null> = {};

    Object.keys(this.globalColors).forEach((key) => {
      const value = this.globalColors[key];
      colorsPayload[key] = value === '' ? null : value;
    });

    payload.append('colors', JSON.stringify(colorsPayload));

    const logoFull = this.logoFiles.global['logo_full'];
    const logoCompact = this.logoFiles.global['logo_compact'];
    const favicon = this.logoFiles.global['favicon'];

    if (logoFull) payload.append('logo_full', logoFull);
    if (logoCompact) payload.append('logo_compact', logoCompact);
    if (favicon) payload.append('favicon', favicon);

    this.brandingService.updateGlobal(payload).subscribe(() => {
      this.brandingService.loadEffective(this.workspaceService.getActiveWorkspaceId());
      this.loadGlobal();
    });
  }

  saveWorkspace(): void {
    if (!this.isSuperAdmin || !this.selectedWorkspaceId) {
      return;
    }
    const payload = new FormData();
    const colorsPayload: Record<string, string | null> = {};

    Object.keys(this.workspaceColors).forEach((key) => {
      const value = this.workspaceColors[key];
      colorsPayload[key] = value === '' ? null : value;
    });

    this.clearedWorkspaceKeys.forEach((key) => {
      colorsPayload[key] = null;
    });

    payload.append('colors', JSON.stringify(colorsPayload));

    const logoFull = this.logoFiles.workspace['logo_full'];
    const logoCompact = this.logoFiles.workspace['logo_compact'];
    const favicon = this.logoFiles.workspace['favicon'];

    if (logoFull) payload.append('logo_full', logoFull);
    if (logoCompact) payload.append('logo_compact', logoCompact);
    if (favicon) payload.append('favicon', favicon);

    this.brandingService.updateWorkspace(this.selectedWorkspaceId, payload).subscribe(() => {
      this.brandingService.loadEffective(this.workspaceService.getActiveWorkspaceId());
      this.loadWorkspace(this.selectedWorkspaceId as number);
    });
  }

  isHexColor(value?: string): boolean {
    if (!value) {
      return false;
    }
    return /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value);
  }

  colorInputValue(value?: string): string {
    if (this.isHexColor(value)) {
      return value as string;
    }
    return '#000000';
  }
}
