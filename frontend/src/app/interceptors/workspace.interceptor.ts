import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpHandler, HttpRequest, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';
import { WorkspaceService } from '../services/workspace/workspace.service';

@Injectable()
export class WorkspaceInterceptor implements HttpInterceptor {
  constructor(private workspaceService: WorkspaceService) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const wsId = this.workspaceService.getActiveWorkspaceId();
    if (!wsId) {
      return next.handle(request);
    }

    const req = request.clone({
      setHeaders: {
        'X-Workspace-Id': String(wsId),
      }
    });

    return next.handle(req);
  }
}
