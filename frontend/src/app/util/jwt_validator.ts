import { Injectable } from '@angular/core';
import * as jwt_decode from 'jwt-decode';
import { CookieService } from 'ngx-cookie-service';

@Injectable()
export class JWTUtils {

    constructor(
        public cookieService: CookieService,
    ) {}

    getUserIDFromJWT()
    {
        var token = this.cookieService.get('token')
        var decodedToken: any = jwt_decode.default(token);
        return decodedToken.user_id;
    }

    getUserPermissionFromJWT(token: string)
    {
        var decodedToken: any = jwt_decode.default(token);
        return decodedToken.permission;
    }

    getUserTypeFromJWT(token: string)
    {
        var decodedToken: any = jwt_decode.default(token);
        return decodedToken.user_type;
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