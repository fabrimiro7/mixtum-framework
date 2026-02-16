// noinspection DuplicatedCode

import { Component, OnInit } from '@angular/core';
import { UntypedFormGroup, UntypedFormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { CookieService } from 'ngx-cookie-service';
import { User } from '../../../models/user';
import { AuthService } from '../../../services/auth/auth.service';
import  *  as CryptoJS from  'crypto-js';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { BrandingService } from 'src/app/services/theme/branding.service';

@Component({
  selector: 'app-login',
  template: `
    <div class="flex min-h-screen bg-white">
      <div class="flex flex-1 flex-col justify-center px-4 py-12 sm:px-6 lg:flex-none lg:px-20 xl:px-24">
        <div class="mx-auto w-full max-w-sm lg:w-96">
          <div>
            <img class="h-10 w-auto" [src]="logoFullUrl" alt="Logo">
            <h2 class="mt-8 text-2xl/9 font-bold tracking-tight text-gray-900">Accedi al tuo account</h2>
            <p class="mt-2 text-sm/6 text-gray-500">
              Serve aiuto?
              <a (click)="resetPassword()" class="font-semibold text-ed-blue hover:text-ed-blue-dark">Recupera la password</a>
            </p>
          </div>

          <div class="mt-10">
            <form [formGroup]="loginForm" (ngSubmit)="loginUser()" #LoginForm="ngForm" class="space-y-6">
              <div>
                <label class="block text-sm/6 font-medium text-gray-900">Email</label>
                <div class="mt-2">
                  <input
                    class="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-ed-blue sm:text-sm/6"
                    placeholder="Inserire email"
                    formControlName="formEmail"
                    type="email"
                    autocomplete="email"
                  >
                </div>
                <div *ngIf="f.formEmail.errors" class="mt-1">
                  <p class="tw-error" *ngIf="f.formEmail.errors.required">L'email è richiesta</p>
                  <p class="tw-error" *ngIf="f.formEmail.errors.pattern">L'email deve essere valida</p>
                  <p class="tw-error" *ngIf="f.formEmail.errors.minlength">L'email deve essere minimo di 4 caratteri</p>
                  <p class="tw-error" *ngIf="f.formEmail.errors.maxlength">L'email deve essere al più di 70 caratteri</p>
                </div>
              </div>

              <div>
                <label class="block text-sm/6 font-medium text-gray-900">Password</label>
                <div class="mt-2 tw-input-addon">
                  <input
                    class="block w-full rounded-md bg-white px-3 py-1.5 pr-10 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-ed-blue sm:text-sm/6"
                    [type]="hide ? 'password' : 'text'"
                    placeholder="Inserire password"
                    formControlName="formPassword"
                    autocomplete="current-password"
                  >
                  <button
                    class="tw-input-icon"
                    (click)="toggleHide()"
                    [attr.aria-label]="'Mostra/Nascondi password'"
                    type="button"
                  >
                    <svg *ngIf="hide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-5" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.477 10.48a3 3 0 0 0 4.243 4.243" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.88 4.24A9.96 9.96 0 0 1 12 4c4.477 0 8.268 2.943 9.542 7a9.965 9.965 0 0 1-4.132 5.226" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6.228 6.228A9.958 9.958 0 0 0 2.458 12c1.274 4.057 5.065 7 9.542 7 1.612 0 3.151-.384 4.518-1.064" />
                    </svg>
                    <svg *ngIf="!hide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="size-5" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                    </svg>
                  </button>
                </div>
                <div *ngIf="f.formPassword.errors" class="mt-1">
                  <p class="tw-error" *ngIf="f.formPassword.errors.required">La password è richiesta</p>
                  <p class="tw-error" *ngIf="f.formPassword.errors.minlength">La password deve essere minimo di 8 caratteri</p>
                </div>
              </div>

              <div class="flex items-center justify-end">
                <button
                  type="button"
                  class="text-sm/6 font-semibold text-ed-blue hover:text-ed-blue-dark"
                  (click)="resetPassword()"
                >
                  Password dimenticata?
                </button>
              </div>

              <div>
                <button
                  type="submit"
                  class="flex w-full justify-center rounded-md bg-ed-blue px-3 py-1.5 text-sm/6 font-semibold text-white shadow-xs hover:bg-ed-blue-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ed-blue"
                >
                  Accedi
                </button>
              </div>
            </form>

            <div *ngIf="submitted && showErrorMessage" class="mt-4 text-sm text-red-600">
              {{ errorMessage }}
            </div>
          </div>
        </div>
      </div>

      <div class="relative hidden w-0 flex-1 lg:block">
        <img
          src="https://images.unsplash.com/photo-1496917756835-20cb06e75b4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=1908&q=80"
          alt=""
          class="absolute inset-0 size-full object-cover"
        >
      </div>
    </div>
  `,
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {

  loginForm: UntypedFormGroup | any;
  submitted = false;
  showErrorMessage = false;
  errorMessage = '';
  email: any = '';
  hide = true;
  logoFullUrl = 'assets/img/ED-LOGO.png';

  public user: any = new User(null!, null!, null!, null!, null!, null!, null!, null!);

  constructor(
    public auth: AuthService,
    public cookieService: CookieService,
    private formBuilder: UntypedFormBuilder,
    private router: Router,
    private brandingService: BrandingService,
  ) {}

  ngOnInit() {
    this.loginForm = this.formBuilder.group({
      // tslint:disable-next-line:max-line-length
      formEmail: ['', [Validators.required, Validators.pattern('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$'), Validators.minLength(4), Validators.maxLength(70)]],
      formPassword: ['', [Validators.required, Validators.minLength(8)]],
    });

    this.brandingService.branding$.subscribe((branding) => {
      this.logoFullUrl = branding?.logo_full || 'assets/img/ED-LOGO.png';
    });
  }

  get f() {
    return this.loginForm?.controls;
  }

  loginUser() {
    this.submitted = true;

    if (this.loginForm?.invalid) {
      return;
    }
    this.auth.login({'email': this.loginForm.value.formEmail, 'password':this.loginForm.value.formPassword})
    .then(
      (data) => {
        if (data['message'] === 'success') {
          this.cookieService.set('token', data['token']);
          this.cookieService.set('refresh_token', data['refresh_token']);
          this.router.navigate(['dashboard']).then();

        } else {
          this.showErrorMessage = true;
          this.errorMessage = 'Credenziali invalide!';
        }
      },
      (error) => {
        console.error('Errore', error);
        this.showErrorMessage = true;
        this.errorMessage = error.error.detail;
      },
    );
  }

  resetPassword() {
    this.router.navigate(['/insert-email']).then();
  }

  alreadyLogged() {
    this.router.navigate(['']).then();
  }

  registerUser(){
    this.router.navigate(['/registration']).then();
  }

  toggleHide() {
    this.hide = !this.hide;
  }
}
