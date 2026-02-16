import { Component, OnInit, ViewChild,AfterViewInit } from '@angular/core';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { ActivatedRoute, Route } from '@angular/router';
import { catchError, finalize } from 'rxjs';
import { Ticket } from 'src/app/models/ticket';
import { DateParser } from 'src/app/util/date_parse';
import { CookieService } from 'ngx-cookie-service';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { Router } from '@angular/router';
import { Project } from 'src/app/models/project';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { FormControl } from '@angular/forms';
import { Message } from 'src/app/models/message';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { AuthService } from 'src/app/services/auth/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MAX_ATTACHMENT_SIZE_MB, MAX_ATTACHMENT_SIZE_BYTES, formatBytesToMb } from 'src/app/constants/attachment';
import { convertUrlsToLinks } from 'src/app/util/safe-html.util';

@Component({
  selector: 'app-ticket-details',
  templateUrl: './ticket-details.component.html',
  styleUrls: ['./ticket-details.component.css']
})
export class TicketDetailsComponent implements OnInit, AfterViewInit {
  @ViewChild('fileInput') fileInput: any;


  data: { displayTime: string; datetime: string | Date; author: string | number; avatar: string; content: string }[] = [];

  submitting = false;
  inputValue = '';

  user: any = [];

  userType: any = '';
  userId: number = 0;

  idTicket: any;
  idProject: any;
  ticket: Ticket = new Ticket(null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null);
  project: Project = new Project(null, null, null, null, null, null, null, null, null, null);

  messages: any = [];
  newMessage: FormControl = new FormControl('');
  attachments: any[] = [];


  constructor(
    private apiTicket: TicketApiService,
    private apiProject: ProjectApiService,
    private activatedRoute: ActivatedRoute,
    public dataParser: DateParser,
    private perm: PermissionService,
    private cookieService: CookieService,
    private router: Router,
    private jwt: JWTUtils,
    private auth: AuthService,
    private sanitizer: DomSanitizer,
    private _snackBar: MatSnackBar,
  ) { }

  ngOnInit(): void {
    var token = this.cookieService.get('token');
    this.userId = this.jwt.getUserIDFromJWT();
    this.userType = this.perm.checkPermission(token);

    this.auth.detailUser(this.userId)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API:', error);
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        this.user = data.data;
      }
    );

    this.activatedRoute.paramMap
      .subscribe((params: any) => {
        if (params.get('id')) {
          this.idTicket = Number(params.get('id'));
          this.ticketDetailsApi();
        }
      });
  }

  ngAfterViewInit(): void {
  }
 
  ticketDetailsApi() {
    this.apiTicket.ticketDetails(this.idTicket)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API ticketDetails:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.ticket = data;
        this.idProject = this.ticket.project.id;
        this.projectDetailsApi();
        this.ticket.opening_date = this.dataParser.ISOToNormalDate(data.opening_date)
        this.ticket.expected_resolution_date = this.dataParser.ISOToNormalDate(data.expected_resolution_date)
        this.ticket.closing_date = this.dataParser.ISOToNormalDate(data.closing_date)
        this.loadMessagesOfTicket();
        this.apiTicket.markTicketAsRead(this.idTicket).subscribe({
          error: (err) => {
            if (err?.status !== 404) {
              console.warn('markTicketAsRead failed:', err?.message || err);
            }
          },
        });
      });
  }
                          
  projectDetailsApi() {
    this.apiProject.projectDetail(this.idProject)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectDetails:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.project = data;
      });
  }


  loadMessagesOfTicket() {
    this.messages = [];
    this.apiTicket.loadMessagesOfTicket(this.idTicket)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API loadMessagesOfTicket:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.messages = data.data;
        
      if (this.ticket?.description && this.ticket?.client) {
        const customMessage = {
          id: 0, 
          author: {
            id: this.ticket.client.id,
            first_name: this.ticket.client.first_name || '',
            last_name: this.ticket.client.last_name || '',
            email: this.ticket.client.email || '',
          },
          text: this.ticket.description,
          attachments: [],
          insert_date: new Date().toISOString(),
        };

        this.messages.unshift(customMessage);
      }
      });
  }

  addMessage(): void {
    this.submitting = true;
    const content = this.inputValue;
    this.inputValue = '';
    setTimeout(() => {
      this.submitting = false;

      let message = {
        author: 1,
        ticket: this.idTicket,
        text: content,
      }

      this.apiTicket.addMessagesOfTicket(this.idTicket, message)
        .pipe(
          catchError(error => {
            console.error('Errore nella chiamata API loadMessagesOfTicket:', error);
            return [];
          })
        );
    }, 800);
  }

  redirectTo(component: String) {
    this.router.navigate([component]);
  }

  sendMessage() {
    var message = new Message(this.newMessage.value)
    this.apiTicket.addMessagesOfTicket(this.idTicket, message)
      .subscribe((data: any) => {
        if (data.message == "success") {
          if (this.attachments.length > 0)
          {
            this.uploadAttachments(data.data.id, "message");
          } else {
            this.loadMessagesOfTicket();
          }
          this.newMessage.reset();
        } else {

        }
      })
  }

  onFileSelected(event: any) {
      const files: FileList = event.target.files;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        this.addAttachment(file);
      }
  }

  uploadAttachments(idElement: any, type: string)  {
    this.attachments.forEach((attachment: any) => {
      const formData = new FormData();
      formData.append('title', attachment.title);
      formData.append('file', attachment.file);
      if (type == "message") {
        this.apiTicket.uploadAttachmentMessage(idElement, formData)
        .pipe(
          finalize(() => {
            this.loadMessagesOfTicket();
          })
        )
        .subscribe((data: any) => {
          if (data.message == "success") {
            this.attachments = [];
          }
        })
      } else if (type == "ticket") {
        this.apiTicket.uploadAttachmentTicket(idElement, formData)
        .pipe(
          finalize(() => {
            this.loadMessagesOfTicket();
          })
        )
        .subscribe((data: any) => {
          if (data.message == "success") {
            this.attachments = [];
          }
        })
      }
    })
  }

  triggerFileInput() {
    this.fileInput.nativeElement.click();
  }

  private addAttachment(file: File) {
    if (file.size > MAX_ATTACHMENT_SIZE_BYTES) {
      this._snackBar.open(
        `${file.name} supera la dimensione massima supportata di ${MAX_ATTACHMENT_SIZE_MB} MB (${formatBytesToMb(file.size)} MB).`,
        'Chiudi',
        { duration: 6000 },
      );
      return;
    }

    this.attachments.push({ title: file.name, file });
  }

  getSafeHtml(content: string): SafeHtml {
    const linkedContent = convertUrlsToLinks(content || '');
    return this.sanitizer.bypassSecurityTrustHtml(linkedContent);
  }

  truncate(text: string, limit: number) {
    const ellipsis = '...';
    return text.length > limit ? text.substring(0, limit) + ellipsis : text;
  }
}
