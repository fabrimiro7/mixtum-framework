import { Component, OnInit } from '@angular/core';
import { catchError } from 'rxjs';
import { User } from 'src/app/models/user';
import { AuthService } from 'src/app/services/auth/auth.service';
import { Router } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-registration',
  templateUrl: './registration.component.html',
  styleUrls: ['./registration.component.css']
})
export class RegistrationComponent implements OnInit {

  userProfile: User | any;
  userProfileForm: UntypedFormGroup | any;
  idUtente: any = '';
  isEditing = false;
  durationInSeconds = 5;

  constructor(
    private auth: AuthService,
    private fb: UntypedFormBuilder,
    private _snackBar: MatSnackBar,
    private router: Router,
    ) { }

  ngOnInit(): void {

    this.userProfileForm = this.fb.group({
      first_name: [{ value: '', disabled: false }, Validators.required],
      last_name: [{ value: '', disabled: false }, Validators.required],
      fiscal_code: [{ value: '', disabled: false }, Validators.required],
      email: [{ value: '', disabled: false }, [Validators.required, Validators.email]],
      phone: [{ value: '', disabled: false }, Validators.required],
      mobile: [{ value: '', disabled: false }, Validators.required],
      password: [{ value: '', disabled: false }, Validators.required],
      username: [{ value: '', disabled: false }],
      user_type: [{ value: 'Persona Fisica', disabled: false }],
    });
  }

  addUser()
  {
    this.auth.registerUser(this.userProfileForm.value)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API:', error);
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        if (data.message == 'success')
        {
          this.openSnackBar("Accedi con l'account appena creato");
          this.router.navigate(['login']).then();
        } else {
          this.openSnackBar("Errore nella creazione dell'utente. Riprova più tardi.");
        }
      }
    );
  }

  back()
  {
    this.router.navigate(['usermanager/users-list']).then();
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  }


}
