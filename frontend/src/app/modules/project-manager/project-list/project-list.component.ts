import { Component, OnInit, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { catchError } from 'rxjs';
import { ApiService } from 'src/app/services/api/api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';
import { DateParser } from 'src/app/util/date_parse';
import { MatSort} from '@angular/material/sort';

@Component({
  selector: 'app-project-list',
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css']
})
export class ProjectListComponent implements OnInit {

  @ViewChild(MatPaginator) paginator: MatPaginator | undefined;
  @ViewChild(MatSort) sort: MatSort | undefined;
  projectList: any = [];
  userList: any = [];
  projectData: any = [];
  userType: any = '';
  displayedColumns: string[] = ['title', 'client', 'insert_date', 'action'];
  

  constructor(   
    private apiProject: ProjectApiService,
    private api: ApiService, 
    private router: Router,
    private perm: PermissionService,
    private cookieService: CookieService,
    private dataParser: DateParser,
  ) { }

  ngOnInit(): void {
    var token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token);
    this.projectListApi();
    this.userListApi();
  }

  projectListApi(){
    this.apiProject.projectList()
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API projectList', error);
        return [];
      })
    )
    .subscribe((data: any) => {
      this.projectList = data.data;
      this.projectData = new MatTableDataSource<any>(this.projectList);
      this.projectData.paginator = this.paginator;
      this.projectData.paginator._intl.itemsPerPageLabel = "Progetti per pagina";
      this.projectData.paginator._intl.nextPageLabel = "Pagina successiva";
      this.projectData.paginator._intl.previousPageLabel = "Pagina precedente";
      this.projectData.sort = this.sort;
    })
  }

  userListApi(){
    this.api.userList()
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API userList', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.userList = data;
      })
    }

    redirectTo(component: String){
      this.router.navigate([component]);
   }
   
   trasformDate(date: string){
    if (date != null){
    return this.dataParser.ISOToNormalDateNoTime(date);
    }
    else return "-";
   }

}
