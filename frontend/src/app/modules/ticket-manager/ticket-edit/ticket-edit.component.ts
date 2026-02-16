import { Component, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { CookieService } from 'ngx-cookie-service';
import { catchError, finalize, of } from 'rxjs';

import { Project } from 'src/app/models/project';
import { Ticket } from 'src/app/models/ticket';
import { User } from 'src/app/models/user';

import { ApiService } from 'src/app/services/api/api.services';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { DateParser } from 'src/app/util/date_parse';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-ticket-edit',
  templateUrl: './ticket-edit.component.html',
  styleUrls: ['./ticket-edit.component.css']
})
export class TicketEditComponent implements OnInit {

  ticket: Ticket = new Ticket(null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);

  ticketForm: UntypedFormGroup | any;

  idTicket: any;
  idProject: any;
  project: Project = new Project(null, null, null, null, null, null, null, null, null, null);

  userType: any;

  workerList: User[] = [];   // lista sviluppatori / staff
  clientList: User[] = [];   // utenti con permesso "user"

  ticketTypes = [
    { value: 'bug', label: 'Bug' },
    { value: 'feature', label: 'Feature' },
    { value: 'evo', label: 'Evolutiva' },
    { value: 'check', label: 'Check' },
    { value: 'aggiornamento', label: 'Aggiornamento' },
  ];

  durationInSeconds = 5;
  messages: any[] = [];
  deleteInProgress = false;

  constructor(
    private apiTicket: TicketApiService,
    private api: ApiService,
    private apiProject: ProjectApiService,
    private activatedRoute: ActivatedRoute,
    private perm: PermissionService,
    private cookieService: CookieService,
    private router: Router,
    private fb: UntypedFormBuilder,
    public dataParser: DateParser,
    private _snackBar: MatSnackBar,
    private sanitizer: DomSanitizer,
    private dialog: MatDialog,
  ) {}

  ngOnInit(): void {

    this.activatedRoute.paramMap.subscribe((params: any) => {
      this.idTicket = Number(params.get('id'));
    });

    const token = this.cookieService.get('token');
    this.userType = this.perm.checkPermission(token);

    // FORM
    this.ticketForm = this.fb.group({
      id: [{value:'', disabled: true}],
      title: ['', Validators.required],
      description: ['', Validators.required],
      ticket_type: [''],
      client: ['', Validators.required],
      project: [{value:'', disabled: true}],
      assignees: [[]],
      priority: [''],
      hours_estimation: [''],
      opening_date: [{value:'', disabled: true}],
      closing_date: [{value:'', disabled: true}],
      cost_estimation: [''],
      status: [''],
      expected_resolution_date: [''],
      expected_action: [{value:'', disabled: true}],
      real_action: [{value:'', disabled: true}],
    });

    this.ticketDetailsApi();
    this.workerListApi();
    this.loadClientsOnly();
    this.loadMessagesOfTicket();
  }

  // ------- API LOAD CLIENTS -------
  loadClientsOnly() {
    this.api.clientList()
      .pipe(
        catchError(error => {
          console.error("Errore caricamento clienti", error);
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.clientList = data
      });
  }

  // ------- LOAD WORKERS -------
  workerListApi() {
    this.api.workerList()
      .pipe(
        catchError(error => {
          console.error('Errore chiamata userList:', error);
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.workerList = data || [];
      });
  }

  // ------- LOAD TICKET DETAILS -------
  ticketDetailsApi() {
    this.apiTicket.ticketDetails(this.idTicket)
      .pipe(
        catchError(error => {
          console.error('Errore ticketDetails:', error);
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (!data) return;

        this.ticket = data;
        this.idProject = data.project.id;

        this.projectDetailsApi();
        this.prepareDates();
        this.patchForm();
      });
  }

  projectDetailsApi() {
    this.apiProject.projectDetail(this.idProject)
      .pipe(
        catchError(error => {
          console.error('Errore projectDetails:', error);
          return of(null);
        })
      )
      .subscribe((data: any) => {
        this.project = data;
      });
  }

  prepareDates() {
    this.ticket.opening_date = this.dataParser.ISOToNormalDate(this.ticket.opening_date);
    this.ticket.expected_resolution_date = this.dataParser.dateTimeLocalConverter(this.ticket.expected_resolution_date);
    this.ticket.closing_date = this.dataParser.ISOToNormalDate(this.ticket.closing_date);
  }

  patchForm() {
    this.ticketForm.patchValue({
      id: this.ticket.id,
      title: this.ticket.title,
      description: this.ticket.description,
      ticket_type: this.ticket.ticket_type,
      client: this.ticket.client?.id,
      project: this.ticket.project.id,
      assignees: this.ticket.assignees,
      priority: this.ticket.priority,
      hours_estimation: this.ticket.hours_estimation,
      opening_date: this.ticket.opening_date,
      closing_date: this.ticket.closing_date,
      cost_estimation: this.ticket.cost_estimation,
      status: this.ticket.status,
      expected_resolution_date: this.ticket.expected_resolution_date,
      expected_action: this.ticket.expected_action,
      real_action: this.ticket.real_action,
    });
  }

  // ------- MESSAGES -------
  loadMessagesOfTicket() {
    this.apiTicket.loadMessagesOfTicket(this.idTicket)
      .pipe(
        catchError(error => {
          console.error('Errore loadMessagesOfTicket:', error);
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.messages = data?.data ?? [];
      });
  }

  // ------- SAVE -------
  saveChangesTicket() {

    if (this.ticketForm.invalid) {
      this.openSnackBar("Dati mancanti o non corretti");
      return;
    }

    this.ticketForm.enable();

    const formValue = this.ticketForm.value;

    const assignees = (formValue.assignees || []).map((a: any) => a.id ?? a);

    const payload = {
      ...formValue,
      assignees,
    };

    if (payload.status === 'resolved' || payload.status === 'closed') {
      payload.closing_date = new Date().toISOString();
    }

    this.apiTicket.editTicket(this.idTicket, payload)
      .pipe(
        catchError(error => {
          console.error('Errore editTicket:', error);
          return of(null);
        })
      )
      .subscribe((data: any) => {
        if (!data || data.message !== 'success') {
          this.openSnackBar("Errore nel salvataggio");
          return;
        }

        this.openSnackBar("Dati salvati correttamente");
        this.redirectTo('/tickets/' + this.idTicket);
      });
  }

  sanitizeMessage(text: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(text || '');
  }

  openDeleteDialog(templateRef: any) {
    const dialogRef = this.dialog.open(templateRef);
    dialogRef.afterClosed().subscribe(result => {
      if (result === 'confirm') {
        this.deleteTicket();
      }
    });
  }

  deleteTicket() {
    this.deleteInProgress = true;
    this.apiTicket.deleteTicket(this.idTicket)
      .pipe(
        finalize(() => {
          this.deleteInProgress = false;
        })
      )
      .subscribe({
        next: (data: any) => {
          if (data?.message === 'success') {
            this.openSnackBar("Ticket eliminato correttamente");
            this.redirectTo('/tickets');
          } else {
            this.openSnackBar("Errore nella cancellazione del ticket");
          }
        },
        error: () => {
          this.openSnackBar("Errore nella cancellazione del ticket");
        }
      });
  }

  compareFn(a: any, b: any) {
    return a && b ? a.id === b.id : false;
  }

  redirectTo(path: string) {
    this.router.navigate([path]);
  }

  openSnackBar(msg: string) {
    this._snackBar.open(msg, "", { duration: this.durationInSeconds * 1000 });
  }
}
