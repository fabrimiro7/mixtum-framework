import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { CookieService } from 'ngx-cookie-service';
import { AuthService } from '../services/auth/auth.service';
import * as jwt_decode from 'jwt-decode';


@Injectable({
  providedIn: 'root',
})
export class isAuthenticatedGuard implements CanActivate {

  private accessTokenExpiration = Date.now() + 3600 * 1000;


  constructor(
    public cookieService: CookieService,
    public router: Router,
    private auth: AuthService,
  ) { }
  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree | any{

      var status = this.isAccessTokenValid(this.cookieService.get('token'))
      if (status == false)
      {
        this.router.navigate(['login']).then();
      } else {
        return true;
      }
  }

  isAccessTokenValid(token: string): boolean {
    try {
      var decodedToken: any = jwt_decode.default(token);
      const expirationTimestamp = decodedToken['exp'] * 1000;
      const currentTimestamp = Date.now();
      
      return currentTimestamp < expirationTimestamp;
    } catch (error) {
      return false;
    }
  }
}
