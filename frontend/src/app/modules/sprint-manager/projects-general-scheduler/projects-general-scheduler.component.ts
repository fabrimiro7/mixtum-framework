import { Component, HostListener, OnInit } from '@angular/core';
import { CdkDragDrop, CdkDragEnd, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, of } from 'rxjs';
import { Phase } from 'src/app/models/phase';
import { SprintApiService } from 'src/app/services/api/sprint-api.service';

@Component({
  selector: 'app-projects-general-scheduler',
  templateUrl: './projects-general-scheduler.component.html',
  styleUrls: ['./projects-general-scheduler.component.css']
})
export class ProjectsGeneralSchedulerComponent implements OnInit {
  phases: Phase[] = [];
  phasesLoading = false;
  viewMode: 'list' | 'board' | 'timeline' = 'list';
  readonly statuses = [
    { value: 'todo', label: 'To Do' },
    { value: 'in_progress', label: 'In corso' },
    { value: 'blocked', label: 'Bloccato' },
    { value: 'done', label: 'Completato' },
    { value: 'canceled', label: 'Annullato' },
  ];
  kanbanListIds: string[] = [];
  phasesByStatusMap: Record<string, Phase[]> = {};
  timelineDays: Date[] = [];
  timelineStartDate: Date | null = null;
  timelineEndDate: Date | null = null;
  readonly timelineDayWidth = 40;
  timelineWidth = 0;
  projectGroups: Array<{ project: { id: number; title: string } | null; phases: Phase[] }> = [];

  constructor(
    private sprintApi: SprintApiService,
    private snackBar: MatSnackBar,
  ) {
    this.kanbanListIds = this.statuses.map(status => `general-phase-kanban-${status.value}`);
    this.resetPhaseBoardColumns();
  }

  ngOnInit(): void {
    this.loadPhases();
  }

  @HostListener('window:resize')
  onWindowResize() {
    this.updateTimelineWidth();
  }

  loadPhases() {
    this.phasesLoading = true;
    this.sprintApi.getAllPhases()
      .pipe(
        catchError(error => {
          console.error('Errore caricamento fasi generali:', error);
          this.phasesLoading = false;
          this.openSnackBar('Errore nel caricamento delle fasi generali.');
          return of([]);
        })
      )
      .subscribe((phases: Phase[]) => {
        this.phases = phases;
        this.phasesLoading = false;
    this.populatePhaseBoard();
      });
  }

  changeView(mode: 'list' | 'board' | 'timeline') {
    this.viewMode = mode;
    if (mode === 'timeline') {
      this.calculatePhaseTimelineRange();
    }
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
          console.error('Errore aggiornamento fase:', error);
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

  private populatePhaseBoard() {
    this.resetPhaseBoardColumns();
    this.phases.forEach(phase => {
      const key = this.phasesByStatusMap[phase.status] ? phase.status : this.statuses[0].value;
      this.phasesByStatusMap[key].push(phase);
    });
    this.buildProjectGroups();
    this.calculatePhaseTimelineRange();
  }

  private resetPhaseBoardColumns() {
    this.phasesByStatusMap = {};
    this.statuses.forEach(status => {
      this.phasesByStatusMap[status.value] = [];
    });
  }

  private buildProjectGroups() {
    const groups = new Map<number | 'unassigned', Phase[]>();
    this.phases.forEach(phase => {
      const projectId = phase.project?.id ?? 'unassigned';
      if (!groups.has(projectId)) {
        groups.set(projectId, []);
      }
      groups.get(projectId)!.push(phase);
    });
    this.projectGroups = Array.from(groups.entries()).map(([key, phases]) => ({
      project: phases[0]?.project ?? (key === 'unassigned' ? null : { id: key as number, title: '' }),
      phases,
    }));
  }

  private calculatePhaseTimelineRange() {
    if (!this.phases.length) {
      this.timelineDays = [];
      this.timelineStartDate = null;
      this.timelineEndDate = null;
      this.timelineWidth = 0;
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

  private updateTimelineWidth() {
    const available = Math.max(window.innerWidth - 240, 320);
    if (!this.timelineDays.length) {
      this.timelineWidth = available;
      return;
    }
    const baseWidth = this.timelineDays.length * this.timelineDayWidth;
    this.timelineWidth = Math.max(baseWidth, available);
  }

  phaseOffsetDays(phase: Phase): number {
    if (!this.timelineStartDate) {
      return 0;
    }
    const start = this.parseDate(phase.start_date);
    if (!start) {
      return 0;
    }
    const diff = start.getTime() - this.timelineStartDate.getTime();
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

  private openSnackBar(message: string) {
    this.snackBar.open(message, '', { duration: 4000 });
  }
}
