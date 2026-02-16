import {Injectable} from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor, HttpErrorResponse
} from '@angular/common/http';
import {catchError, Observable, switchMap, throwError} from 'rxjs';
import {AuthService} from "../services/auth/auth.service";
import { CookieService } from 'ngx-cookie-service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  refresh = false;

  constructor(
    private authService: AuthService,
    private cookieService: CookieService,
    ) {
  }

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<any> {

    if (this.isLoginRequest(request) || this.isLogoutRequest(request) || 
          this.isRefreshRequest(request) || this.isRegisterRequest(request) || this.isPasswordRequest(request))
    {
      return next.handle(request.clone({}));
    }

    const token = this.cookieService.get('token') || this.authService.accessToken;
    if (!token) {
      return next.handle(request.clone({}));
    }

    const req = request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });

    return next.handle(req).pipe(catchError((err: HttpErrorResponse): any => {
      if ((err.status === 401 || err.status === 403)) {
        return this.authService.refresh().pipe(
          switchMap((res: any) => {
            if (res.token)
            {
              this.authService.accessToken = res.token;
              this.cookieService.set('token', res.token);
            }
            return next.handle(request.clone({
              setHeaders: {
                Authorization: `Bearer ${this.authService.accessToken}`
              }
            }));
          })
        );
      } else {
        return next.handle(request.clone({
          setHeaders: {
            Authorization: `Bearer ${this.authService.accessToken}`
          }
        }));
      }
    }));
  }


  private isRefreshRequest(request: HttpRequest<any>): boolean {
    // Verifica se la richiesta è una chiamata di refresh del token
    // Implementa la logica in base alla tua implementazione dell'API di refresh del token
    // Ad esempio, controlla l'URL o il corpo della richiesta per determinare se è una chiamata di refresh
    return request.url.includes('/refresh/');
  }

  private isLoginRequest(request: HttpRequest<any>): boolean {
    // Verifica se la richiesta è una chiamata di refresh del token
    // Implementa la logica in base alla tua implementazione dell'API di refresh del token
    // Ad esempio, controlla l'URL o il corpo della richiesta per determinare se è una chiamata di refresh
    return request.url.includes('/login/');
  }

  private isLogoutRequest(request: HttpRequest<any>): boolean {
    // Verifica se la richiesta è una chiamata di refresh del token
    // Implementa la logica in base alla tua implementazione dell'API di refresh del token
    // Ad esempio, controlla l'URL o il corpo della richiesta per determinare se è una chiamata di refresh
    return request.url.includes('/logout/');
  }

  private isRegisterRequest(request: HttpRequest<any>): boolean {
    // Verifica se la richiesta è una chiamata di registrazione dell'utente
    // Implementa la logica in base alla tua implementazione dell'API di refresh del token
    // Ad esempio, controlla l'URL o il corpo della richiesta per determinare se è una chiamata di refresh
    return request.url.includes('/register/');
  }

  private isPasswordRequest(request: HttpRequest<any>): boolean {
    // Verifica se la richiesta è una chiamata di recupero password dell'utente
    // Implementa la logica in base alla tua implementazione dell'API di refresh del token
    // Ad esempio, controlla l'URL o il corpo della richiesta per determinare se è una chiamata di refresh
    return request.url.includes('/reset/');
  }

}
