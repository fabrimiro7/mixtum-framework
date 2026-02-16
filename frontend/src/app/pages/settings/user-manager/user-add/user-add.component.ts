import { Component, OnInit } from '@angular/core';
import { catchError, of } from 'rxjs';
import { User } from 'src/app/models/user';
import { AuthService } from 'src/app/services/auth/auth.service';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { Router } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators, AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-user-add',
  templateUrl: './user-add.component.html',
  styleUrls: ['./user-add.component.css']
})
export class UserAddComponent implements OnInit {

  userProfile: User | any;
  userProfileForm: UntypedFormGroup | any;
  idUtente: any = '';
  isEditing = false;
  durationInSeconds = 5;

  constructor(
    private auth: AuthService,
    private jwt: JWTUtils,
    private fb: UntypedFormBuilder,
    private _snackBar: MatSnackBar,
    private router: Router,
  ) { }

  // Group-level validator: ensure password and password_confirm match
  private passwordsMatchValidator: ValidatorFn = (group: AbstractControl): ValidationErrors | null => {
    const pass = group.get('password')?.value;
    const confirm = group.get('password_confirm')?.value;
    if (!pass || !confirm) return null; // don't show mismatch until both are filled
    return pass === confirm ? null : { passwordMismatch: true };
  };

  ngOnInit(): void {
    // Create reactive form with field-level validators + group-level password matcher
    this.userProfileForm = this.fb.group({
      first_name: [{ value: '', disabled: false }, Validators.required],
      last_name: [{ value: '', disabled: false }, Validators.required],
      fiscal_code: [{ value: '', disabled: false }, Validators.required],
      email: [{ value: '', disabled: false }, [Validators.required, Validators.email]],
      phone: [{ value: '', disabled: false }, Validators.required],
      mobile: [{ value: '', disabled: false }, Validators.required],
      password: [{ value: '', disabled: false }, Validators.required],
      password_confirm: [{ value: '', disabled: false }, Validators.required],
      username: [{ value: '', disabled: false }],
    }, { validators: this.passwordsMatchValidator });
  }

  // Convenient getters for template bindings
  get f(): Record<string, AbstractControl> {
    return (this.userProfileForm?.controls || {}) as Record<string, AbstractControl>;
  }

  get passwordMismatch(): boolean {
    return !!this.userProfileForm?.errors?.['passwordMismatch'];
  }

  addUser(): void {
    // Guard: if form invalid, mark touched and stop
    if (!this.userProfileForm || this.userProfileForm.invalid) {
      this.userProfileForm?.markAllAsTouched();
      this.openSnackBar("Controlla i campi evidenziati.");
      return;
    }

    this.isEditing = true;

    // Prepare payload: remove password_confirm before sending to API
    const payload = { ...this.userProfileForm.value };

    this.auth.createUser(payload)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API:', error);
          this.isEditing = false;
          this.openSnackBar("Errore nella creazione dell'utente. Riprova più tardi.");
          return of(null);
        })
      )
      .subscribe(
        (data: any) => {
          if (data && data.message === 'success') {
            this.openSnackBar("Utente creato correttamente");
            this.router.navigate(['usermanager/users-list']).then();
          } else if (data) {
            // API responded but not success
            this.isEditing = false;
            this.userProfileForm.enable();
            this.openSnackBar("Errore nella creazione dell'utente. Riprova più tardi.");
          }
          // if data is null, catchError already handled UI state
        }
      );
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", { duration: this.durationInSeconds * 1000 });
  }

  redirectTo(component: string) {
    this.router.navigate([component]);
  }
}
