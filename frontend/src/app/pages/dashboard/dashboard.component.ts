import { Component, OnInit } from '@angular/core';
import { ApiService } from 'src/app/services/api/api.services';
import { catchError, forkJoin, finalize } from 'rxjs';
import { Router } from '@angular/router';
import { User } from 'src/app/models/user';
import { AuthService } from 'src/app/services/auth/auth.service';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { Project } from 'src/app/models/project';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { Ticket } from 'src/app/models/ticket';
import { MatTableDataSource } from '@angular/material/table';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {

  cards: any[] = [];
  idUser: any = '';
  userProfile: User | any;
  avatarUrl: string = 'assets/img/avatar.jpeg';
  projectList: Project[] = [];
  ticketList: Ticket[] = [];
  dataSource: any = [];
  displayedColumns: string[] = ['title', 'status', 'action'];
  userType: any = '';
  showPaymentsCard = true;
  articleList: any[] = [];
  loading = true;


  constructor(
    private api: ApiService,
    private apiProject: ProjectApiService,
    private apiTicket: TicketApiService,
    private perm: PermissionService,
    private cookieService: CookieService,
    private router: Router,
    private auth: AuthService,
    private jwt: JWTUtils,
  ) { }

  ngOnInit(): void {
    this.loading = true;
    this.idUser = this.jwt.getUserIDFromJWT();
    var token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token);
    this.showPaymentsCard = this.userType !== 'Employee';
    
    // Carica tutti i dati in parallelo e disattiva loading quando completati
    forkJoin({
      user: this.auth.detailUser(this.idUser).pipe(catchError(error => {
        console.error('Errore nella chiamata API detailUser:', error);
        return [{ data: null }];
      })),
      projects: this.apiProject.projectsFromUser(this.idUser).pipe(catchError(error => {
        console.error('Errore nella chiamata API projectFromUser', error);
        return [{ data: [] }];
      })),
      tickets: this.apiTicket.ticketList({
        page: 1,
        page_size: 10,
        ordering: '-opening_date'
      }).pipe(catchError(error => {
        console.error('Errore nella chiamata API ticketList', error);
        return [{ data: [], results: [] }];
      })),
      articles: this.api.getArticles().pipe(catchError(error => {
        console.error('Errore nella chiamata API getArticles', error);
        return [];
      }))
    }).pipe(
      finalize(() => {
        this.loading = false;
      })
    ).subscribe(({ user, projects, tickets, articles }) => {
      // User details
      if (user.data) {
        this.userProfile = user.data;
        if (user.data.avatar !== null) {
          this.avatarUrl = user.data.avatar;
        }
      }
      
      // Projects
      this.projectList = projects.data || [];
      
      // Tickets
      const ticketData = tickets.data || tickets.results || [];
      this.ticketList = ticketData;
      this.dataSource = new MatTableDataSource(ticketData);
      
      // Articles
      this.articleList = articles || [];
    });
  }

  // Metodi rimossi - ora tutto gestito in ngOnInit con forkJoin

  getStatusClass(status: string): string {
    switch (status) {
      case 'open':
        return 'status-open';
      case 'in_progress':
        return 'status-in-progress';
      case 'resolved':
        return 'status-resolved';
      case 'closed':
        return 'status-closed';
      default:
        return '';
    }
  }

  redirectTo(component: String){
    this.router.navigate([component]);
  }  

 truncate(text: string, limit: number){
  const ellipsis = '...';
  return text.length > limit ? text.substring(0, limit) + ellipsis : text;
 }

}
