import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { environment } from 'src/environments/django';
import { BrandingEffective, BrandingSettings } from 'src/app/models/branding';

@Injectable({
  providedIn: 'root'
})
export class BrandingService {
  private baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;
  private brandingSubject = new BehaviorSubject<BrandingEffective | null>(null);
  branding$ = this.brandingSubject.asObservable();

  constructor(private http: HttpClient) {}

  loadEffective(workspaceId?: number | null): void {
    let params = new HttpParams();
    if (workspaceId) {
      params = params.set('workspace_id', workspaceId.toString());
    }
    const url = `${this.baseUrl}/api/branding/effective/`;
    this.http.get<BrandingEffective>(url, { params }).subscribe((data) => {
      this.applyTheme(data);
      this.updateFavicon(data.favicon || 'favicon.ico');
      this.brandingSubject.next(data);
    });
  }

  applyTheme(data: BrandingEffective): void {
    if (typeof document === 'undefined') {
      return;
    }
    const root = document.documentElement;
    Object.entries(data.colors || {}).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });
  }

  updateFavicon(url: string): void {
    if (typeof document === 'undefined') {
      return;
    }
    let link = document.querySelector("link[rel='icon']") as HTMLLinkElement | null;
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
    }
    link.href = url;
  }

  getGlobal(): Observable<BrandingSettings> {
    const url = `${this.baseUrl}/api/branding/global/`;
    return this.http.get<BrandingSettings>(url);
  }

  updateGlobal(payload: FormData): Observable<BrandingSettings> {
    const url = `${this.baseUrl}/api/branding/global/`;
    return this.http.patch<BrandingSettings>(url, payload);
  }

  getWorkspace(workspaceId: number): Observable<BrandingSettings> {
    const url = `${this.baseUrl}/api/branding/workspace/${workspaceId}/`;
    return this.http.get<BrandingSettings>(url);
  }

  updateWorkspace(workspaceId: number, payload: FormData): Observable<BrandingSettings> {
    const url = `${this.baseUrl}/api/branding/workspace/${workspaceId}/`;
    return this.http.patch<BrandingSettings>(url, payload);
  }
}
