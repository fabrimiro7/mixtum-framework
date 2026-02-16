import { Component, OnInit } from '@angular/core';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';
import { Workspace } from 'src/app/models/workspace';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-workspace-selector',
  templateUrl: './workspace-selector.component.html',
  styleUrls: ['./workspace-selector.component.css']
})
export class WorkspaceSelectorComponent implements OnInit {
  workspaces: Workspace[] = [];
  selectedId: number | null = null;
  loading = false;
  error = '';

  constructor(
    private workspaceService: WorkspaceService,
  ) {}

  ngOnInit(): void {
    this.selectedId = this.workspaceService.getActiveWorkspaceId();
    this.loadWorkspaces();
  }

  loadWorkspaces(): void {
    this.loading = true;
    this.error = '';
    this.workspaceService.listWorkspaces()
      .pipe(
        catchError(() => {
          this.error = 'Errore nel caricamento workspace.';
          return of([] as Workspace[]);
        })
      )
      .subscribe((data: Workspace[]) => {
        this.workspaces = Array.isArray(data) ? data : [];
        this.loading = false;
      });
  }

  onWorkspaceChange(): void {
    this.workspaceService.setActiveWorkspace(this.selectedId);
  }
}
