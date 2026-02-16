import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IsAdminGuard } from 'src/app/guards/is-admin.guard';
import { ProjectAddComponent } from './project-add/project-add.component';
import { ProjectDetailsComponent } from './project-details/project-details.component';
import { ProjectEditComponent } from './project-edit/project-edit.component';
import { ProjectListComponent } from './project-list/project-list.component';
import { IsUserGuard } from 'src/app/guards/is-user.guard';

const routes: Routes = [
  { path: '', canActivate: [IsUserGuard], component: ProjectListComponent, data: { breadcrumb: 'Lista Progetti' }, },
  { path: 'add', canActivate: [IsAdminGuard], component: ProjectAddComponent, data: { breadcrumb: 'Aggiungi Progetto' },},
  { path: 'edit/:id', canActivate: [IsAdminGuard], component: ProjectEditComponent, data: { breadcrumb: 'Modifica Progetto' },},
  { path: ':id', canActivate: [IsUserGuard], component: ProjectDetailsComponent, data: { breadcrumb: 'Dettagli Progetto' },},
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ProjectManagerRoutingModule { }
