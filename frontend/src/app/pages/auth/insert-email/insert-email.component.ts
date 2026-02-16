import { Component, OnInit } from '@angular/core';
import { catchError } from 'rxjs';
import { AuthService } from 'src/app/services/auth/auth.service';
import { Router } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-insert-email',
  templateUrl: './insert-email.component.html',
  styleUrls: ['./insert-email.component.scss']
})
export class InsertEmailComponent implements OnInit {

  userResetPasswordForm: UntypedFormGroup | any;
  durationInSeconds = 5;

  constructor(
    private auth: AuthService,
    private fb: UntypedFormBuilder,
    private _snackBar: MatSnackBar,
    private router: Router,
    ) { }

  ngOnInit(): void {

    this.userResetPasswordForm = this.fb.group({
      email: [{ value: '', disabled: false }, [Validators.required, Validators.email]],
    });
  }

  sendResetLink()
  {
    this.auth.sendEmail(this.userResetPasswordForm.value)
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
          this.openSnackBar("Email inviata correttamente");
          this.router.navigate(['login']).then();
        } else {
          this.openSnackBar("Errore nell'invio del link di recupero. Riprova più tardi.");
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
