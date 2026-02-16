import { Component, HostListener, OnInit } from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, of } from 'rxjs';
import { CdkDragDrop, CdkDragEnd, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { Project } from 'src/app/models/project';
import { Link } from 'src/app/models/link';
import { ApiService } from 'src/app/services/api/api.services';
import { LinkApiService } from 'src/app/services/api/link-api.service';
import { ProjectApiService } from 'src/app/services/api/project-api.services';
import { DateParser } from 'src/app/util/date_parse';
import { TicketApiService } from 'src/app/services/api/ticket-api.services';
import { SprintApiService } from 'src/app/services/api/sprint-api.service';
import { Task } from 'src/app/models/task';
import { Phase } from 'src/app/models/phase';
import { Report } from 'src/app/models/report';
import { ReportApiService } from 'src/app/services/api/report-api.service';
import { PermissionService } from 'src/app/services/auth/permission.service';
import { CookieService } from 'ngx-cookie-service';

@Component({
  selector: 'app-project-details',
  templateUrl: './project-details.component.html',
  styleUrls: ['./project-details.component.css']
})
export class ProjectDetailsComponent implements OnInit {

  projectID: number = 0;
  project!: Project;
  projectLinks: Link[] = [];
  linksLoading = false;
  linkFormVisible = false;
  linkSubmitting = false;
  linkForm: UntypedFormGroup;
  editingLink: Link | null = null;
  contentTypeLoading = false;
  projectContentTypeId: number | null = null;
  private fetchingContentType = false;
  private pendingContentTypeCallbacks: Array<() => void> = [];
  linkFieldErrors: Record<string, string[]> = {};
  linkGeneralError = '';
  activeTabIndex = 0;
  readonly tabKeys: string[] = ['details', 'tickets', 'tasks', 'phases', 'reports'];
  tabsLoaded = {
    details: true,
    tickets: false,
    tasks: false,
    phases: false,
    reports: false,
  };
  reports: Report[] = [];
  reportsLoading = false;
  reportForm: UntypedFormGroup;
  reportFormVisible = false;
  editingReport: Report | null = null;
  reportSaving = false;
  reportFormError = '';
  currentPermission: string | null = null;
  canManageLinkActions = false;
  showTaskTab = true;
  showPhaseTab = true;
  readonly reportVisibilityOptions = [
    { value: 'SuperAdmin', label: 'SuperAdmin' },
    { value: 'Admin', label: 'Admin' },
    { value: 'Employee', label: 'Employee' },
    { value: 'Utente', label: 'Utente' },
  ];
  tasks: Task[] = [];
  tasksLoading = false;
  tasksViewMode: 'list' | 'board' | 'timeline' = 'list';
  readonly taskStatuses = [
    { value: 'todo', label: 'To Do' },
    { value: 'in_progress', label: 'In corso' },
    { value: 'blocked', label: 'Bloccato' },
    { value: 'done', label: 'Completato' },
    { value: 'canceled', label: 'Annullato' },
  ];
  readonly taskPriorities = [
    { value: 'low', label: 'Bassa' },
    { value: 'medium', label: 'Media' },
    { value: 'high', label: 'Alta' },
  ];
  taskFormVisible = false;
  taskSubmitting = false;
  taskForm: UntypedFormGroup;
  phaseFormVisible = false;
  phaseSubmitting = false;
  phaseForm: UntypedFormGroup;
  userList: { id: number; first_name?: string; last_name?: string }[] = [];
  kanbanListIds: string[] = [];
  tasksByStatusMap: Record<string, Task[]> = {};
  timelineDays: Date[] = [];
  timelineStartDate: Date | null = null;
  timelineEndDate: Date | null = null;
  readonly timelineDayWidth = 40;
  timelineWidth = 0;
  phases: Phase[] = [];
  phasesLoading = false;
  phasesViewMode: 'list' | 'board' | 'timeline' = 'list';
  phaseKanbanListIds: string[] = [];
  phasesByStatusMap: Record<string, Phase[]> = {};
  phaseTimelineDays: Date[] = [];
  phaseTimelineStartDate: Date | null = null;
  phaseTimelineEndDate: Date | null = null;
  phaseTimelineWidth = 0;
  readonly linkLabels = [
    { value: 'google_drive', label: 'Google Drive' },
    { value: 'figma', label: 'Figma' },
    { value: 'google_doc', label: 'Google Doc' },
    { value: 'google_spreadsheet', label: 'Google Spreadsheet' },
    { value: 'github', label: 'GitHub' },
    { value: 'wetransfer', label: 'WeTransfer' },
    { value: 'altro', label: 'Altro' },
  ];

  get userListWithNone(): Array<{ id: number | null; first_name?: string; last_name?: string }> {
    return [{ id: null, first_name: '— Nessuno —', last_name: '' }, ...this.userList];
  }
  
  constructor(

    private activatedRoute: ActivatedRoute,
    private apiProject: ProjectApiService,
    private dataParser: DateParser,
    private router: Router,
    private linkApi: LinkApiService,
    private fb: UntypedFormBuilder,
    private snackBar: MatSnackBar,
    private ticketApi: TicketApiService,
    private sprintApi: SprintApiService,
    private reportApi: ReportApiService,
    private permissionService: PermissionService,
    private cookieService: CookieService,
    private api: ApiService,

  ) {
    this.linkForm = this.fb.group({
      id: [null],
      title: ['', [Validators.required, Validators.maxLength(255)]],
      url: ['', [
        Validators.required,
        Validators.maxLength(1000),
        Validators.pattern(/^(https?:\/\/)[^\s$.?#].[^\s]*$/i),
      ]],
      description: [''],
      label: ['altro', Validators.required],
    });
    this.reportForm = this.fb.group({
      report_title: ['', [Validators.required, Validators.maxLength(1000)]],
      report_description: ['', [Validators.required, Validators.minLength(2)]],
      visible_roles: [this.reportVisibilityOptions.map(option => option.value), Validators.required],
    });
    this.kanbanListIds = this.taskStatuses.map(status => `kanban-${status.value}`);
    this.resetTaskBoardColumns();
    this.phaseKanbanListIds = this.taskStatuses.map(status => `phase-kanban-${status.value}`);
    this.resetPhaseBoardColumns();
    this.taskForm = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(200)]],
      description: [''],
      assignee: [null as number | null],
      priority: ['medium'],
      status: ['todo'],
      start_date: [null as string | null],
      due_date: [null as string | null],
      estimate_hours: [null as number | null],
    });
    this.phaseForm = this.fb.group({
      title: ['', [Validators.required, Validators.maxLength(200)]],
      description: [''],
      owner: [null as number | null],
      priority: ['medium'],
      status: ['todo'],
      start_date: [null as string | null],
      due_date: [null as string | null],
    });
  }

  @HostListener('window:resize')
  onWindowResize() {
    this.updateTimelineWidth();
    this.updatePhaseTimelineWidth();
  }

  ngOnInit(): void {
    this.setCurrentPermission();

    this.activatedRoute.paramMap
      .subscribe((params: any) => {
        const paramId = params.get('id');
        if (paramId) {
          this.projectID = Number(paramId);
          this.projectDetailsAPI();
          this.loadProjectLinks();
          this.fetchProjectContentType();
        }
      });

    this.activatedRoute.queryParamMap
      .subscribe(params => {
        const visibleTabs = this.getVisibleTabs();
        const tabKey = params.get('tab');
        const tabIndex = tabKey ? visibleTabs.indexOf(tabKey) : 0;
        this.activeTabIndex = tabIndex >= 0 ? tabIndex : 0;
        const activeKey = visibleTabs[this.activeTabIndex] || visibleTabs[0];
        this.activateTabByKey(activeKey);
      });
  }

  projectDetailsAPI(){
    this.apiProject.projectDetail(this.projectID)
      .pipe(
        catchError(error => {
          console.error('Errore nella chiamata API projectDetail:', error);
          return [];
        })
      )
      .subscribe((data: any) => {
        this.project = data;
        this.project.insert_date = this.dataParser.ISOToNormalDate(data.insert_date)
      });
  }

  loadProjectLinks() {
    if (!this.projectID) {
      return;
    }
    this.linksLoading = true;
    this.linkApi.list({
      app_label: 'project_manager',
      model: 'project',
      object_id: this.projectID
    })
    .pipe(
      catchError(error => {
        console.error('Errore nel caricamento dei link progetto:', error);
        this.openSnackBar('Errore nel caricamento dei link.');
        this.linksLoading = false;
        return of([]);
      })
    )
    .subscribe((response: any) => {
      this.projectLinks = Array.isArray(response) ? response : response?.results || [];
      this.linksLoading = false;
    });
  }

  startAddLink() {
    const openForm = () => {
      this.editingLink = null;
      this.linkForm.reset({ label: 'altro' });
      this.clearLinkErrors();
      this.linkFormVisible = true;
    };

    if (!this.projectContentTypeId) {
      this.fetchProjectContentType(openForm);
      return;
    }

    openForm();
  }

  startEditLink(link: Link) {
    this.editingLink = link;
    this.linkFormVisible = true;
    this.clearLinkErrors();
    this.linkForm.patchValue({
      id: link.id,
      title: link.title,
      url: link.url,
      description: link.description,
      label: link.label,
    });
  }

  cancelLinkForm() {
    this.linkForm.reset({ label: 'altro' });
    this.linkFormVisible = false;
    this.linkSubmitting = false;
    this.editingLink = null;
    this.clearLinkErrors();
  }

  saveLink() {
    this.clearLinkErrors();
    if (this.linkForm.invalid) {
      this.linkForm.markAllAsTouched();
      return;
    }

    if (!this.editingLink && !this.projectContentTypeId) {
      this.openSnackBar('Non è stato possibile identificare il tipo di contenuto. Riprova.');
      this.fetchProjectContentType();
      return;
    }

    const formValue = this.linkForm.getRawValue();
    const payload = {
      title: formValue.title,
      url: formValue.url,
      description: formValue.description,
      label: formValue.label,
      object_id: this.projectID,
    };

    this.linkSubmitting = true;
    const request$ = this.editingLink
      ? this.linkApi.update(this.editingLink.id, payload)
      : this.linkApi.create({
          ...payload,
          content_type_id: this.projectContentTypeId,
        });

    request$
      .pipe(
        catchError(error => {
          console.error('Errore salvataggio link progetto:', error);
          this.handleLinkErrors(error);
          this.linkSubmitting = false;
          return of(null);
        })
      )
      .subscribe((result: any) => {
        if (!result) {
          this.linkSubmitting = false;
          return;
        }
        this.openSnackBar(this.editingLink ? 'Link aggiornato.' : 'Link aggiunto.');
        this.cancelLinkForm();
        this.loadProjectLinks();
        this.linkSubmitting = false;
      });
  }

  deleteLink(link: Link) {
    const confirmDelete = window.confirm(`Eliminare il link "${link.title}"?`);
    if (!confirmDelete) {
      return;
    }

    this.linkApi.delete(link.id)
      .pipe(
        catchError(error => {
          console.error('Errore eliminazione link progetto:', error);
          this.openSnackBar('Errore nell\'eliminazione del link.');
          return of(null);
        })
      )
      .subscribe((result: any) => {
        if (result === null) {
          return;
        }
        this.openSnackBar('Link eliminato.');
        this.loadProjectLinks();
      });
  }

  trackByLink(_index: number, link: Link) {
    return link.id;
  }

  //Function to redirect to a component based on what button the user click 
  redirectTo(component: String) {
    this.router.navigate([component]);
  }

  openNewTicket() {
    this.router.navigate(['tickets/add/'], {
      queryParams: { project: this.projectID }
    });
  }

  private openSnackBar(message: string) {
    this.snackBar.open(message, '', { duration: 4000 });
  }

  private setCurrentPermission() {
    const token = this.cookieService.get('token');
    if (!token) {
      this.currentPermission = null;
      return;
    }
    try {
      this.currentPermission = this.permissionService.checkPermission(token);
      const isRestricted = this.currentPermission === 'Utente' || this.currentPermission === 'Employee';
      this.canManageLinkActions = !isRestricted;
      this.showTaskTab = !isRestricted;
      this.showPhaseTab = !isRestricted;
    } catch {
      this.currentPermission = null;
    }
  }

  canManageReports(): boolean {
    return this.currentPermission === 'SuperAdmin' || this.currentPermission === 'Admin';
  }

  private clearLinkErrors() {
    this.linkFieldErrors = {};
    this.linkGeneralError = '';
  }

  private handleLinkErrors(error: any) {
    if (error?.status === 400 && error.error && typeof error.error === 'object') {
      let hasFieldError = false;
      Object.entries(error.error).forEach(([key, value]) => {
        const messages = Array.isArray(value) ? value : [value as string];
        if (this.linkForm.get(key)) {
          this.linkFieldErrors[key] = messages;
          hasFieldError = true;
        } else {
          this.linkGeneralError = messages.join(' ');
        }
      });
      if (!hasFieldError && !this.linkGeneralError) {
        this.linkGeneralError = 'Alcuni campi contengono errori.';
      }
    } else {
      this.openSnackBar('Errore nel salvataggio del link.');
    }
  }

  private fetchProjectContentType(callback?: () => void) {
    if (callback) {
      this.pendingContentTypeCallbacks.push(callback);
    }

    if (this.projectContentTypeId) {
      this.flushContentTypeCallbacks();
      return;
    }

    if (this.fetchingContentType) {
      return;
    }

    this.contentTypeLoading = true;
    this.fetchingContentType = true;

    this.linkApi.getContentTypeId('project_manager', 'project')
      .pipe(
        catchError(error => {
          console.error('Errore nel recupero del content type per i link:', error);
          this.openSnackBar('Impossibile determinare il tipo di link per il progetto.');
          this.fetchingContentType = false;
          this.contentTypeLoading = false;
          this.pendingContentTypeCallbacks = [];
          return of(null);
        })
      )
      .subscribe((id: number | null) => {
        this.fetchingContentType = false;
        this.contentTypeLoading = false;
        if (id) {
          this.projectContentTypeId = id;
          this.flushContentTypeCallbacks();
        }
      });
  }

  private flushContentTypeCallbacks() {
    const callbacks = [...this.pendingContentTypeCallbacks];
    this.pendingContentTypeCallbacks = [];
    callbacks.forEach(cb => cb());
  }

  onTabChange(index: number) {
    const visibleTabs = this.getVisibleTabs();
    const tabKey = visibleTabs[index] || visibleTabs[0];
    const newIndex = visibleTabs.indexOf(tabKey);
    this.activeTabIndex = newIndex >= 0 ? newIndex : 0;
    this.router.navigate([], {
      relativeTo: this.activatedRoute,
      queryParams: { tab: tabKey === 'details' ? null : tabKey },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    this.activateTabByKey(tabKey);
  }

  private getVisibleTabs(): string[] {
    const tabs = ['details', 'tickets'];
    if (this.showTaskTab) tabs.push('tasks');
    if (this.showPhaseTab) tabs.push('phases');
    tabs.push('reports');
    return tabs;
  }

  private activateTabByKey(key: string) {
    const visibleTabs = this.getVisibleTabs();
    const normalizedKey = visibleTabs.includes(key) ? key : visibleTabs[0] || this.tabKeys[0];

    if (normalizedKey === 'details') {
      this.tabsLoaded.details = true;
      return;
    }
    if (normalizedKey === 'tickets' && !this.tabsLoaded.tickets) {
      this.tabsLoaded.tickets = true;
    }
    if (normalizedKey === 'tasks' && !this.tabsLoaded.tasks) {
      this.tabsLoaded.tasks = true;
      this.loadTasksTab();
    }
    if (normalizedKey === 'phases' && !this.tabsLoaded.phases) {
      this.tabsLoaded.phases = true;
      this.loadPhasesTab();
    }
    if (normalizedKey === 'reports' && !this.tabsLoaded.reports) {
      this.tabsLoaded.reports = true;
      this.loadReportsTab();
    }
  }

  private loadUserList() {
    if (this.userList.length > 0) {
      return;
    }
    this.api.userList()
      .pipe(
        catchError(error => {
          console.error('Errore caricamento utenti:', error);
          return of([]);
        })
      )
      .subscribe((data: any) => {
        this.userList = Array.isArray(data) ? data : [];
      });
  }

  startAddTask() {
    this.taskForm.reset({
      title: '',
      description: '',
      assignee: null,
      priority: 'medium',
      status: 'todo',
      start_date: null,
      due_date: null,
      estimate_hours: null,
    });
    this.loadUserList();
    this.taskFormVisible = true;
  }

  cancelTaskForm() {
    this.taskFormVisible = false;
    this.taskSubmitting = false;
  }

  saveTask() {
    if (this.taskForm.invalid || !this.projectID) {
      this.taskForm.markAllAsTouched();
      return;
    }
    this.taskSubmitting = true;
    const v = this.taskForm.getRawValue();
    const payload: Record<string, unknown> = {
      title: v.title,
      description: v.description || '',
      assignee: v.assignee || null,
      priority: v.priority || 'medium',
      status: v.status || 'todo',
      start_date: this.toDateString(v.start_date),
      due_date: this.toDateString(v.due_date),
      estimate_hours: v.estimate_hours != null && v.estimate_hours !== '' ? Number(v.estimate_hours) : null,
    };
    this.ticketApi.createTask(this.projectID, payload as Partial<Task>)
      .pipe(
        catchError(error => {
          console.error('Errore creazione task:', error);
          this.openSnackBar(error?.error?.detail || 'Errore nella creazione del task.');
          this.taskSubmitting = false;
          return of(null);
        })
      )
      .subscribe((created: Task | null) => {
        this.taskSubmitting = false;
        if (!created) return;
        this.tasks.unshift(created);
        this.populateTaskBoard();
        this.taskFormVisible = false;
        this.openSnackBar('Task aggiunto.');
      });
  }

  startAddPhase() {
    this.phaseForm.reset({
      title: '',
      description: '',
      owner: null,
      priority: 'medium',
      status: 'todo',
      start_date: null,
      due_date: null,
    });
    this.loadUserList();
    this.phaseFormVisible = true;
  }

  cancelPhaseForm() {
    this.phaseFormVisible = false;
    this.phaseSubmitting = false;
  }

  savePhase() {
    if (this.phaseForm.invalid || !this.projectID) {
      this.phaseForm.markAllAsTouched();
      return;
    }
    this.phaseSubmitting = true;
    const v = this.phaseForm.getRawValue();
    const payload: Record<string, unknown> = {
      title: v.title,
      description: v.description || '',
      owner: v.owner || null,
      priority: v.priority || 'medium',
      status: v.status || 'todo',
      start_date: this.toDateString(v.start_date),
      due_date: this.toDateString(v.due_date),
    };
    this.sprintApi.createPhase(this.projectID, payload as Partial<Phase>)
      .pipe(
        catchError(error => {
          console.error('Errore creazione fase:', error);
          this.openSnackBar(error?.error?.detail || 'Errore nella creazione della fase.');
          this.phaseSubmitting = false;
          return of(null);
        })
      )
      .subscribe((created: Phase | null) => {
        this.phaseSubmitting = false;
        if (!created) return;
        this.phases.unshift(created);
        this.populatePhaseBoard();
        this.phaseFormVisible = false;
        this.openSnackBar('Fase aggiunta.');
      });
  }

  private toDateString(value: Date | string | null | undefined): string | null {
    if (value == null || value === '') return null;
    if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
    const d = value instanceof Date ? value : new Date(value);
    return isNaN(d.getTime()) ? null : this.formatDate(d);
  }

  private loadTasksTab() {
    if (this.tasksLoading || !this.projectID) {
      return;
    }
    this.tasksLoading = true;
    this.ticketApi.getProjectTasks(this.projectID)
      .pipe(
        catchError(error => {
          console.error('Errore nel caricamento dei task:', error);
          this.openSnackBar('Errore nel caricamento dei task.');
          this.tasksLoading = false;
          return of([]);
        })
      )
      .subscribe((tasks: Task[]) => {
        this.tasks = tasks;
        this.tasksLoading = false;
        this.populateTaskBoard();
      });
  }

  private loadPhasesTab() {
    if (this.phasesLoading || !this.projectID) {
      return;
    }
    this.phasesLoading = true;
    this.sprintApi.getProjectPhases(this.projectID)
      .pipe(
        catchError(error => {
          console.error('Errore nel caricamento delle fasi:', error);
          this.openSnackBar('Errore nel caricamento delle fasi di progetto.');
          this.phasesLoading = false;
          return of([]);
        })
      )
      .subscribe((phases: Phase[]) => {
        this.phases = phases;
        this.phasesLoading = false;
        this.populatePhaseBoard();
      });
  }

  private loadReportsTab() {
    if (this.reportsLoading || !this.projectID) {
      return;
    }
    this.reportsLoading = true;
    this.reportApi.getProjectReports(this.projectID)
      .pipe(
        catchError(error => {
          console.error('Errore nel caricamento dei report:', error);
          this.openSnackBar('Errore nel caricamento dei report.');
          this.reportsLoading = false;
          return of([]);
        })
      )
      .subscribe((reports: Report[]) => {
        this.reports = reports;
        this.reportsLoading = false;
      });
  }

  startAddReport() {
    this.editingReport = null;
    this.reportForm.reset({
      report_title: '',
      report_description: '',
      visible_roles: this.reportVisibilityOptions.map(option => option.value),
    });
    this.reportFormVisible = true;
    this.reportFormError = '';
  }

  startEditReport(report: Report) {
    this.editingReport = report;
    this.reportForm.patchValue({
      report_title: report.report_title || '',
      report_description: report.report_description || '',
      visible_roles: report.visible_roles?.length ? report.visible_roles : [],
    });
    this.reportFormVisible = true;
    this.reportFormError = '';
  }

  cancelReportForm() {
    this.reportFormVisible = false;
    this.editingReport = null;
    this.reportFormError = '';
  }

  saveReport() {
    if (this.reportForm.invalid || !this.projectID) {
      this.reportForm.markAllAsTouched();
      return;
    }
    this.reportSaving = true;
    this.reportFormError = '';
    const payload = {
      report_title: this.reportForm.value.report_title,
      report_description: this.reportForm.value.report_description,
      visible_roles: this.reportForm.value.visible_roles || [],
      report_project: this.projectID,
    };
    const request$ = this.editingReport
      ? this.reportApi.updateReport(this.editingReport.id, payload)
      : this.reportApi.createReport(payload);
    request$
      .pipe(
        catchError(error => {
          console.error('Errore nel salvataggio del report:', error);
          this.reportFormError = 'Errore nel salvataggio del report.';
          this.reportSaving = false;
          return of(null);
        })
      )
      .subscribe((savedReport: Report | null) => {
        this.reportSaving = false;
        if (!savedReport) {
          return;
        }
        if (this.editingReport) {
          const index = this.reports.findIndex(item => item.id === savedReport.id);
          if (index > -1) {
            this.reports[index] = savedReport;
          }
          this.openSnackBar('Report aggiornato.');
        } else {
          this.reports.unshift(savedReport);
          this.openSnackBar('Report aggiunto.');
        }
        this.reportFormVisible = false;
        this.editingReport = null;
      });
  }

  changeTaskView(mode: 'list' | 'board' | 'timeline') {
    this.tasksViewMode = mode;
    if (mode === 'timeline') {
      this.calculateTimelineRange();
    }
  }

  changePhaseView(mode: 'list' | 'board' | 'timeline') {
    this.phasesViewMode = mode;
    if (mode === 'timeline') {
      this.calculatePhaseTimelineRange();
    }
  }

  onTaskDrop(event: CdkDragDrop<Task[]>, newStatus: string) {
    const currentList = event.container.data;
    const previousList = event.previousContainer.data;

    if (event.previousContainer === event.container) {
      moveItemInArray(currentList, event.previousIndex, event.currentIndex);
      return;
    }

    transferArrayItem(previousList, currentList, event.previousIndex, event.currentIndex);

    const movedTask = currentList[event.currentIndex];
    const previousStatus = movedTask.status;
    if (previousStatus === newStatus) {
      return;
    }

    movedTask.status = newStatus;

    this.ticketApi.updateTask(movedTask.id, { status: newStatus })
      .pipe(
        catchError(error => {
          console.error('Errore nell\'aggiornamento del task:', error);
          this.openSnackBar('Errore nell\'aggiornamento del task.');
          const currentIndex = currentList.indexOf(movedTask);
          if (currentIndex > -1) {
            currentList.splice(currentIndex, 1);
          }
          previousList.splice(event.previousIndex, 0, movedTask);
          movedTask.status = previousStatus;
          return of(null);
        })
      )
      .subscribe((updated: Task | null) => {
        if (!updated) {
          return;
        }
        movedTask.status_display = updated.status_display || movedTask.status;
      });
  }

  onPhaseDrop(event: CdkDragDrop<Phase[]>, newStatus: string) {
    const currentList = event.container.data;
    const previousList = event.previousContainer.data;

    if (event.previousContainer === event.container) {
      moveItemInArray(currentList, event.previousIndex, event.currentIndex);
      return;
    }

    transferArrayItem(previousList, currentList, event.previousIndex, event.currentIndex);

    const movedPhase = currentList[event.currentIndex];
    const previousStatus = movedPhase.status;
    if (previousStatus === newStatus) {
      return;
    }

    movedPhase.status = newStatus;

    this.sprintApi.updatePhase(movedPhase.id, { status: newStatus })
      .pipe(
        catchError(error => {
          console.error('Errore nell\'aggiornamento della fase:', error);
          this.openSnackBar('Errore nell\'aggiornamento della fase.');
          const currentIndex = currentList.indexOf(movedPhase);
          if (currentIndex > -1) {
            currentList.splice(currentIndex, 1);
          }
          previousList.splice(event.previousIndex, 0, movedPhase);
          movedPhase.status = previousStatus;
          return of(null);
        })
      )
      .subscribe((updated: Phase | null) => {
        if (!updated) {
          return;
        }
        movedPhase.status_display = updated.status_display || movedPhase.status;
      });
  }

  onTimelineDragEnded(event: CdkDragEnd, task: Task) {
    const deltaDays = Math.round(event.distance.x / this.timelineDayWidth);
    event.source.reset();
    if (!deltaDays) {
      return;
    }

    const start = this.parseDate(task.start_date);
    const end = this.parseDate(task.due_date);
    if (!start || !end) {
      return;
    }

    const newStart = this.addDays(start, deltaDays);
    const newEnd = this.addDays(end, deltaDays);
    task.start_date = this.formatDate(newStart);
    task.due_date = this.formatDate(newEnd);

    this.ticketApi.updateTask(task.id, { start_date: task.start_date, due_date: task.due_date })
      .pipe(
        catchError(error => {
          console.error('Errore aggiornamento date task:', error);
          this.openSnackBar('Errore nell\'aggiornamento delle date del task.');
          task.start_date = this.formatDate(start);
          task.due_date = this.formatDate(end);
          return of(null);
        })
      )
      .subscribe((updated: Task | null) => {
        if (updated) {
          task.start_date = updated.start_date || task.start_date;
          task.due_date = updated.due_date || task.due_date;
          this.calculateTimelineRange();
        }
      });
  }

  onPhaseTimelineDragEnded(event: CdkDragEnd, phase: Phase) {
    const deltaDays = Math.round(event.distance.x / this.timelineDayWidth);
    event.source.reset();
    if (!deltaDays) {
      return;
    }

    const start = this.parseDate(phase.start_date);
    const end = this.parseDate(phase.due_date);
    if (!start || !end) {
      return;
    }

    const newStart = this.addDays(start, deltaDays);
    const newEnd = this.addDays(end, deltaDays);
    phase.start_date = this.formatDate(newStart);
    phase.due_date = this.formatDate(newEnd);

    this.sprintApi.updatePhase(phase.id, { start_date: phase.start_date, due_date: phase.due_date })
      .pipe(
        catchError(error => {
          console.error('Errore aggiornamento date fase:', error);
          this.openSnackBar('Errore nell\'aggiornamento della fase.');
          phase.start_date = this.formatDate(start);
          phase.due_date = this.formatDate(end);
          return of(null);
        })
      )
      .subscribe((updated: Phase | null) => {
        if (updated) {
          phase.start_date = updated.start_date || phase.start_date;
          phase.due_date = updated.due_date || phase.due_date;
          this.calculatePhaseTimelineRange();
        }
      });
  }

  private resetTaskBoardColumns() {
    this.tasksByStatusMap = {};
    this.taskStatuses.forEach(column => {
      this.tasksByStatusMap[column.value] = [];
    });
  }

  private populateTaskBoard() {
    this.resetTaskBoardColumns();
    this.tasks.forEach(task => {
      const key = this.tasksByStatusMap[task.status] ? task.status : this.taskStatuses[0].value;
      this.tasksByStatusMap[key].push(task);
    });
    this.calculateTimelineRange();
  }

  private calculateTimelineRange() {
    if (!this.tasks.length) {
      this.timelineDays = [];
      this.timelineStartDate = null;
      this.timelineEndDate = null;
      this.timelineWidth = 0;
      return;
    }

    let minDate: Date | null = null;
    let maxDate: Date | null = null;
    this.tasks.forEach(task => {
      this.ensureTaskDates(task);
      const start = this.parseDate(task.start_date);
      const end = this.parseDate(task.due_date);
      if (!start || !end) {
        return;
      }
      if (!minDate || start < minDate) {
        minDate = new Date(start);
      }
      if (!maxDate || end > maxDate) {
        maxDate = new Date(end);
      }
    });

    if (!minDate || !maxDate) {
      this.timelineDays = [];
      this.timelineWidth = 0;
      return;
    }

    const minRangeEnd = new Date(minDate);
    minRangeEnd.setMonth(minRangeEnd.getMonth() + 6);
    maxDate = new Date(minDate);
    if (maxDate && maxDate < minRangeEnd) {
      maxDate = minRangeEnd;
    }

    minDate = this.addDays(minDate, -3);
    maxDate = this.addDays(maxDate, 3);
    this.timelineStartDate = minDate;
    this.timelineEndDate = maxDate;

    const days: Date[] = [];
    let cursor = new Date(minDate);
    while (cursor <= maxDate) {
      days.push(new Date(cursor));
      cursor = this.addDays(cursor, 1);
    }
    this.timelineDays = days;
    this.updateTimelineWidth();
  }

  taskOffsetDays(task: Task): number {
    if (!this.timelineStartDate) {
      return 0;
    }
    const start = this.parseDate(task.start_date);
    if (!start) {
      return 0;
    }
    const diff = start.getTime() - this.timelineStartDate.getTime();
    return Math.max(0, Math.round(diff / (1000 * 60 * 60 * 24)));
  }

  taskDurationDays(task: Task): number {
    const start = this.parseDate(task.start_date);
    const end = this.parseDate(task.due_date);
    if (!start || !end) {
      return 1;
    }
    const diff = Math.max(0, Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)));
    return diff + 1;
  }

  private ensureTaskDates(task: Task) {
    const today = new Date();
    let start = this.parseDate(task.start_date) || this.parseDate(task.due_date) || today;
    let end = this.parseDate(task.due_date) || start;
    if (end < start) {
      end = new Date(start);
    }
    task.start_date = this.formatDate(start);
    task.due_date = this.formatDate(end);
  }

  private parseDate(value?: string | null): Date | null {
    if (!value) {
      return null;
    }
    const parsed = new Date(value);
    return isNaN(parsed.getTime()) ? null : parsed;
  }

  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  private addDays(date: Date, days: number): Date {
    const copy = new Date(date);
    copy.setDate(copy.getDate() + days);
    return copy;
  }

  private updateTimelineWidth() {
    const available = Math.max(window.innerWidth - 240, 320);
    if (!this.timelineDays.length) {
      this.timelineWidth = available;
      return;
    }
    const baseWidth = this.timelineDays.length * this.timelineDayWidth;
    this.timelineWidth = Math.max(baseWidth, available);
  }

  private resetPhaseBoardColumns() {
    this.phasesByStatusMap = {};
    this.taskStatuses.forEach(column => {
      this.phasesByStatusMap[column.value] = [];
    });
  }

  private populatePhaseBoard() {
    this.resetPhaseBoardColumns();
    this.phases.forEach(phase => {
      const key = this.phasesByStatusMap[phase.status] ? phase.status : this.taskStatuses[0].value;
      this.phasesByStatusMap[key].push(phase);
    });
    this.calculatePhaseTimelineRange();
  }

  private calculatePhaseTimelineRange() {
    if (!this.phases.length) {
      this.phaseTimelineDays = [];
      this.phaseTimelineStartDate = null;
      this.phaseTimelineEndDate = null;
      this.phaseTimelineWidth = 0;
      return;
    }

    let minDate: Date | null = null;
    let maxDate: Date | null = null;
    this.phases.forEach(phase => {
      this.ensurePhaseDates(phase);
      const start = this.parseDate(phase.start_date);
      const end = this.parseDate(phase.due_date);
      if (!start || !end) {
        return;
      }
      if (!minDate || start < minDate) {
        minDate = new Date(start);
      }
      if (!maxDate || end > maxDate) {
        maxDate = new Date(end);
      }
    });

    if (!minDate || !maxDate) {
      this.phaseTimelineDays = [];
      this.phaseTimelineWidth = 0;
      return;
    }

    const minRangeEnd = new Date(minDate);
    minRangeEnd.setMonth(minRangeEnd.getMonth() + 6);
    maxDate = new Date(minDate);
    if (maxDate && maxDate < minRangeEnd) {
      maxDate = minRangeEnd;
    }

    minDate = this.addDays(minDate, -3);
    maxDate = this.addDays(maxDate, 3);
    this.phaseTimelineStartDate = minDate;
    this.phaseTimelineEndDate = maxDate;

    const days: Date[] = [];
    let cursor = new Date(minDate);
    while (cursor <= maxDate) {
      days.push(new Date(cursor));
      cursor = this.addDays(cursor, 1);
    }
    this.phaseTimelineDays = days;
    this.updatePhaseTimelineWidth();
  }

  phaseOffsetDays(phase: Phase): number {
    if (!this.phaseTimelineStartDate) {
      return 0;
    }
    const start = this.parseDate(phase.start_date);
    if (!start) {
      return 0;
    }
    const diff = start.getTime() - this.phaseTimelineStartDate.getTime();
    return Math.max(0, Math.round(diff / (1000 * 60 * 60 * 24)));
  }

  phaseDurationDays(phase: Phase): number {
    const start = this.parseDate(phase.start_date);
    const end = this.parseDate(phase.due_date);
    if (!start || !end) {
      return 1;
    }
    const diff = Math.max(0, Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)));
    return diff + 1;
  }

  private ensurePhaseDates(phase: Phase) {
    const today = new Date();
    let start = this.parseDate(phase.start_date) || this.parseDate(phase.due_date) || today;
    let end = this.parseDate(phase.due_date) || start;
    if (end < start) {
      end = new Date(start);
    }
    phase.start_date = this.formatDate(start);
    phase.due_date = this.formatDate(end);
  }

  private updatePhaseTimelineWidth() {
    const available = Math.max(window.innerWidth - 240, 320);
    if (!this.phaseTimelineDays.length) {
      this.phaseTimelineWidth = available;
      return;
    }
    const baseWidth = this.phaseTimelineDays.length * this.timelineDayWidth;
    this.phaseTimelineWidth = Math.max(baseWidth, available);
  }

}
