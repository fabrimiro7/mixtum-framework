import { Component, OnInit } from '@angular/core';
import { BrandingService } from './services/theme/branding.service';

interface SideNavToggle {
  screenWidth: number;
  collapsed: boolean;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'ed-platform';

  isSideNavCollapsed = false;
  screenWidth = 0;

  constructor(private brandingService: BrandingService) {}

  ngOnInit(): void {
    const raw = typeof window !== 'undefined' ? window.localStorage.getItem('activeWorkspaceId') : null;
    const workspaceId = raw ? parseInt(raw, 10) : null;
    this.brandingService.loadEffective(Number.isFinite(workspaceId as number) ? workspaceId : null);
  }

  onToggleSideNav(data: SideNavToggle): void {
    this.screenWidth = data.screenWidth;
    this.isSideNavCollapsed = data.collapsed;
  }
}
