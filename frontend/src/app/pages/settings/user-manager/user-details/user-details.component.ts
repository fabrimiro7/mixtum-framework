import { Component, OnInit } from '@angular/core';
import { catchError } from 'rxjs';
import { User } from 'src/app/models/user';
import { AuthService } from 'src/app/services/auth/auth.service';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { Router, ActivatedRoute } from '@angular/router';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-user-details',
  templateUrl: './user-details.component.html',
  styleUrls: ['./user-details.component.css']
})
export class UserDetailsComponent implements OnInit {

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
    private activatedRoute: ActivatedRoute,
    ) { }

  ngOnInit(): void {

    this.activatedRoute.paramMap.subscribe((params: any) => {
      if (params.get('id')) {
        this.idUtente = Number(params.get('id'));
      }
    });
    this.userProfileForm = this.fb.group({
      first_name: [{ value: '', disabled: true }, Validators.required],
      last_name: [{ value: '', disabled: true }, Validators.required],
      fiscal_code: [{ value: '', disabled: true }, Validators.required],
      email: [{ value: '', disabled: true }, [Validators.required, Validators.email]],
      phone: [{ value: '', disabled: true }, Validators.required],
      mobile: [{ value: '', disabled: true }, Validators.required],
    });


    this.auth.detailUser(this.idUtente)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API:', error);
          return [];
        })
      )
      .subscribe(
        (data: any) => {
          this.userProfile = data.data;
          this.userProfileForm.patchValue({
              first_name: this.userProfile.first_name,
              last_name: this.userProfile.last_name,
              fiscal_code: this.userProfile.fiscal_code,
              email: this.userProfile.email,
              phone: this.userProfile.phone,
              mobile: this.userProfile.mobile,
              avatar: this.userProfile.avatar,
            });
        }
      );
  }

  editProfile()
  {
    this.isEditing = true;
    this.userProfileForm.enable();
  }

  closeEditProfile()
  {
    this.isEditing = false;
    this.userProfileForm.disable();
  }

  saveChangesProfile()
  {
    if (this.userProfileForm.valid) {
      this.auth.editUser(this.idUtente, this.userProfileForm.value)
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
            this.isEditing = false;
            this.userProfileForm.disable();
            this.openSnackBar("Dati salvati correttamente");
          } else {
            this.isEditing = false;
            this.userProfileForm.disable();
            this.openSnackBar("Errore nel salvataggio dei dati. Riprova più tardi.");
          }
        }
      );
    } else {
      this.openSnackBar("Dati inseriti non corretti o mancanti");
    }
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "", {duration: this.durationInSeconds * 1000});
  }

}
