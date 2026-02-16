import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from 'src/environments/django';
import { Workspace } from 'src/app/models/workspace';
import { BrandingService } from 'src/app/services/theme/branding.service';

@Injectable({
  providedIn: 'root'
})
export class WorkspaceService {
  private baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;
  private storageKey = 'activeWorkspaceId';
  private activeWorkspaceSubject = new BehaviorSubject<number | null>(this.getStoredWorkspaceId());
  activeWorkspaceId$ = this.activeWorkspaceSubject.asObservable();

  constructor(private http: HttpClient, private brandingService: BrandingService) {}

  listWorkspaces(): Observable<Workspace[]> {
    const url = `${this.baseUrl}/api/workspace/workspaces/`;
    return this.http.get<Workspace[]>(url);
  }

  setActiveWorkspace(id: number | null): void {
    if (typeof window !== 'undefined') {
      if (id) {
        window.localStorage.setItem(this.storageKey, id.toString());
        window.localStorage.setItem('currentWorkspaceId', id.toString());
      } else {
        window.localStorage.removeItem(this.storageKey);
        window.localStorage.removeItem('currentWorkspaceId');
      }
    }
    this.activeWorkspaceSubject.next(id);
    this.brandingService.loadEffective(id);
  }

  getActiveWorkspaceId(): number | null {
    return this.activeWorkspaceSubject.value;
  }

  private getStoredWorkspaceId(): number | null {
    if (typeof window === 'undefined') {
      return null;
    }
    const raw = window.localStorage.getItem(this.storageKey) || window.localStorage.getItem('currentWorkspaceId');
    if (!raw) {
      return null;
    }
    const parsed = parseInt(raw, 10);
    return Number.isFinite(parsed) ? parsed : null;
  }
}
