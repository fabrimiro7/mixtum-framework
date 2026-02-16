import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { JWTUtils } from '../util/jwt_validator';
import { CookieService } from 'ngx-cookie-service';
import { PermissionService } from '../services/auth/permission.service';

@Injectable({
  providedIn: 'root'
})
export class IsAdminGuard implements CanActivate {

  constructor(
    private cookieService: CookieService,
    private router: Router,
    private jwt: JWTUtils,
    private permission: PermissionService
  ) { }

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree | any {
      
      var token = this.cookieService.get('token');
      var status = this.jwt.isAccessTokenValid(token)
      if (status == false)
      {
        this.router.navigate(['login']).then();
      } else {
        var permission = this.permission.checkPermission(token);
        if (permission == 'Admin' || permission == 'SuperAdmin')
        {
          return true;
        } else {
          this.router.navigate(['']).then();
        }
      }
  }
  
}
