import { Component, Inject, OnInit } from '@angular/core';
import { MatTableDataSource } from '@angular/material/table';
import { MatDialog, MatDialogRef, MatDialogModule, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { catchError } from 'rxjs';
import { AuthService } from 'src/app/services/auth/auth.service';
import { MatButtonModule } from '@angular/material/button';

export interface DialogData {
  idUser: string;
}

@Component({
  selector: 'app-users-list',
  templateUrl: './users-list.component.html',
  styleUrls: ['./users-list.component.css']
})
export class UsersListComponent implements OnInit {
  
  displayedColumns: string[] = ['id', 'email', 'first_name', 'last_name', 'actions'];
  dataSource: any = [];

  constructor(
    private auth: AuthService,
    private router: Router,
    public dialog: MatDialog
  ) { }

  ngOnInit(): void {
    this.listUserAPI();
  }

  
  listUserAPI()
  {
    this.auth.listUser()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API:', error);
          return [];
        })
      )
      .subscribe(
        (data: any) => {
          this.dataSource = new MatTableDataSource(data);
        }
      );
  }


  deleteUser(id: any)
  {
    this.openDialog(id)
  }

  openDialog(id: string): void {
    this.dialog.open(UserDeleteDialog, {data: {idUser: id}});
  }

  addUser()
  {
    this.router.navigate(['usermanager/user-add']).then();
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }

}

@Component({
  selector: 'delete-user-dialog',
  templateUrl: 'delete-user-dialog.html',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule],
})
export class UserDeleteDialog {
  constructor(
    public dialogRef: MatDialogRef<UserDeleteDialog>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData,
    private auth: AuthService,
    private router: Router,
    ) {}

    deleteUserDef()
    {
      this.auth.deleteUser(this.data.idUser)
        .pipe(
          catchError(error => {
            console.error('Errore nella chiamata API:', error);
            return [];
          })
        )
        .subscribe(
          (data: any) => {
            window.location.reload()
          }
        );
    }

  
}