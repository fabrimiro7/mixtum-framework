import { Component, OnInit } from '@angular/core';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { Router, ActivatedRoute } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { JWTUtils } from 'src/app/util/jwt_validator';
import { catchError } from 'rxjs';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { MAX_ATTACHMENT_SIZE_MB, MAX_ATTACHMENT_SIZE_BYTES, formatBytesToMb } from 'src/app/constants/attachment';

@Component({
  selector: 'app-ticket-add',
  templateUrl: './ticket-add.component.html',
  styleUrls: ['./ticket-add.component.css']
})
export class TicketAddComponent implements OnInit {
  
  ticketForm: UntypedFormGroup | any;
  idUtente: any = '';
  durationInSeconds = 5;
  projectList: any = [];
  preselectedProjectId: number | null = null;

  attachments: any[] = [];
  selectedPriority: 'low' | 'medium' | 'high' | null = null;
  isDragOver = false;

  constructor(
    private api: TicketApiService,
    private router: Router,
    private route: ActivatedRoute,
    private _snackBar: MatSnackBar,
    private fb: UntypedFormBuilder,
    private apiProject: ProjectApiService,
    private jwt: JWTUtils,
  ) { }

  ngOnInit(): void {
    this.idUtente = this.jwt.getUserIDFromJWT();

    // Leggi il query parameter project se presente
    this.route.queryParams.subscribe(params => {
      const projectId = params['project'];
      if (projectId) {
        this.preselectedProjectId = Number(projectId);
      }
    });

    this.ticketForm = this.fb.group({
      title: [{value:'', disabled: false}, Validators.required],
      description: [{value:'', disabled: false}, Validators.required],
      client: [{value:'', disabled: false}],
      project: [{value:'', disabled: false}, Validators.required],
      expected_action: [{value:'', disabled: false}],
      real_action: [{value:'', disabled: false}],
      priority: [{value:'', disabled:false}, Validators.required],

    })
    
    this.userProjectList();
    this.ticketForm.get('client').setValue(this.idUtente);
  }

  //saving the thicket data into db
  addTicket(){
    
    this.api.addTicket(this.ticketForm.value)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API addTicket:', error);
        return [];
      })
    )
    .subscribe(
      (data: any) => {
        if (data.message == 'success')
        {
          this.uploadAttachments(data.data.id);
          this.router.navigate(['tickets'])
        }
        else {
          this.openSnackBar("Errore nella creazione del Ticket")
        }
      }
    )
  
  }
  
  //retriving user's project list
  userProjectList(){
    this.projectList = [];
    this.apiProject.projectsFromUser(this.idUtente)
    .pipe(
      catchError(error => {
        console.error('Errore nella chiamata API projectFromUser', error);
        return [];
      })
    )
     .subscribe(
      (data: any) => {
        this.projectList = data.data;
        // Imposta il progetto dal query parameter se presente e valido
        if (this.preselectedProjectId && this.projectList.some((p: any) => p.id == this.preselectedProjectId)) {
          this.ticketForm.get('project')?.setValue(this.preselectedProjectId);
        }
      });

  }

  openSnackBar(message: string) {
    this._snackBar.open(message, "Ticket aggiunto correttamente", {duration: this.durationInSeconds * 1000});
  } 

  redirectTo(component: String){
    this.router.navigate([component]);
  }

  onFileSelected(event: any) {
    const files: FileList = event.target.files;
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      this.addAttachment(file);
    }
  }

  uploadAttachments(idTicket: any) {
    this.attachments.forEach((attachment: any) => {
      const formData = new FormData();
      formData.append('title', attachment.title);
      formData.append('file', attachment.file);
      this.api.uploadAttachmentTicket(idTicket, formData)
      .subscribe((data: any) => {
        if (data.message == "success")
        {
          console.log("success")
        }
      })
    })
  }

  selectPriority(level: 'low' | 'medium' | 'high') {
    this.selectedPriority = level;
    this.ticketForm.patchValue({ priority: level });
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver = false;

    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      const files = event.dataTransfer.files;

      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        this.addAttachment(file);
      }
    }
  }

  private addAttachment(file: File) {
    if (file.size > MAX_ATTACHMENT_SIZE_BYTES) {
      this._snackBar.open(
        `${file.name} supera la dimensione massima consentita di ${MAX_ATTACHMENT_SIZE_MB} MB (${formatBytesToMb(file.size)} MB).`,
        'Chiudi',
        { duration: 6000 },
      );
      return;
    }

    this.attachments.push({ title: file.name, file });
  }


}
