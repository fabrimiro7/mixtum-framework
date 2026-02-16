import { Injectable } from '@angular/core';
import { JWTUtils } from 'src/app/util/jwt_validator';


enum PermissionLevel {
    SuperAdmin = 'SuperAdmin',
    Admin = 'Admin',
    Utente = 'Utente',
    Employee = 'Employee',
}

@Injectable()
export class PermissionService {

    constructor(
        private jwt: JWTUtils,
      ) {}
    
    /**
     * Function to check and assign permissions to logged user
     */
    checkPermission(token: string)
    {
        var permission_level = this.jwt.getUserPermissionFromJWT(token);

        if (permission_level == 100)
            return PermissionLevel.SuperAdmin;
        else if (permission_level == 50)
            return PermissionLevel.Admin;
        else if (permission_level == 10)
            return PermissionLevel.Utente;
        else if (permission_level == 5)
            return PermissionLevel.Employee;
        else
            throw new Error("Nessun livello di permesso");
    }


    /**
     * Function to check and assign user type to logged user
     */
    checkUserType(token: string)
    {
        var user_type = this.jwt.getUserTypeFromJWT(token);
        return user_type;
    }
}