import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NewPassword } from 'src/app/models/newPassword';
import { AuthService } from 'src/app/services/auth/auth.service';
import { MustMatch } from 'src/app/util/must_match_validator';

@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss']
})
export class ResetPasswordComponent implements OnInit {

  resetPasswordForm: UntypedFormGroup | any;
  disableButton = false;
  submitted = false;
  showErrorMessage = false;
  errorMessage = '';

  password: any;

  public newPassword: NewPassword = new NewPassword(null!, null!, null!, null!, null!);

  id = this.actRoute.snapshot.params['id'];
  token = this.actRoute.snapshot.params['token'];

  constructor(
    public auth: AuthService,
    private formBuilder: UntypedFormBuilder,
    public actRoute: ActivatedRoute,
    public router: Router,
  ) {}

  ngOnInit() {
    this.resetPasswordForm = this.formBuilder.group({
      formPassword: ['', [Validators.required, Validators.minLength(8)]],
      formConfirmPassword: ['', Validators.required],
    }, {
      validator: MustMatch('formPassword', 'formConfirmPassword'),
    });
  }

  get f() {
    return this.resetPasswordForm.controls;
  }

  reset() {
    this.submitted = true;
    if (this.resetPasswordForm.invalid) {
      return;
    }
    //TO DO
    /*
    this.newPassword['id'] = this.id;
    this.newPassword['token'] = this.token;

  
    this.auth.resetPassword(this.newPassword)
      .then(
        (data: any) => {
          if (data.message === 'success') {
          } else {
            this.showErrorMessage = true;
            this.errorMessage = 'Reset password invalida!';
          }
        },
        (error: any) => {
          console.error('Errore', error);
          this.showErrorMessage = true;
          this.errorMessage = 'Errore API resetPassword';
        },
      )
    ;*/
  }

}
