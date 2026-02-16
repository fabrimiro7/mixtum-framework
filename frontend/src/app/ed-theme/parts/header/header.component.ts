import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { AuthService } from 'src/app/services/auth/auth.service';
import { Router } from '@angular/router';
import { catchError, pipe } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { ButtonClickService } from 'src/app/services/utils/button-click.service';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { WorkspaceService } from 'src/app/services/workspace/workspace.service';
import { Workspace } from 'src/app/models/workspace';


@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class HeaderComponent implements OnInit {

  avatarUrl: string = '';
  workspaces: Workspace[] = [];
  activeWorkspaceId: number | null = null;
  showWorkspaceSelector = false;

  constructor(
    private auth: AuthService,
    private router: Router,
    public cookieService: CookieService,
    private buttonClickService: ButtonClickService,
    private jwt: JWTUtils,
    private workspaceService: WorkspaceService,
  ) { }

  ngOnInit(): void {
    this.auth.detailUser(this.jwt.getUserIDFromJWT())
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API:', error);
          return [];
        })
      )
      .subscribe(
        (data: any) => {
          this.avatarUrl = data.data.avatar;
        }
      );

    this.workspaceService.activeWorkspaceId$.subscribe((id) => {
      this.activeWorkspaceId = id;
    });

    this.workspaceService.listWorkspaces()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API (workspaces):', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.workspaces = data || [];
        this.showWorkspaceSelector = this.workspaces.length > 1;
        if (this.workspaces.length > 0 && !this.activeWorkspaceId) {
          this.workspaceService.setActiveWorkspace(this.workspaces[0].id);
        }
      });
    this.buttonClickService.clickEvent$.subscribe(() => {
      const targetButton = document.getElementById('targetButton');
      if (targetButton) {
        targetButton.click();
      }
    });
  }

  logout()
  {
    this.auth.logout()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.cookieService.set('token', '');
        this.cookieService.set('refresh_token', '');
        this.router.navigate(['login']).then(); 
      });
  }

  account()
  {
    this.router.navigate(['profile']).then();
  }

  toggleMenu()
  {
    this.buttonClickService.clickButton();
  }

  onWorkspaceChange(workspaceId: number): void {
    this.workspaceService.setActiveWorkspace(workspaceId);
  }
}
