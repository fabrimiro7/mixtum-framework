import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IsAdminGuard } from 'src/app/guards/is-admin.guard';
import { isAuthenticatedGuard } from 'src/app/guards/isAuthenticated.guard';
import { TutorialAddComponent } from './tutorial-add/tutorial-add.component';
import { TutorialDetailsComponent } from './tutorial-details/tutorial-details.component';
import { TutorialEditComponent } from './tutorial-edit/tutorial-edit.component';
import { AcademyComponent } from './academy/academy.component';
import { CategoriesAddComponent } from './categories-add/categories-add.component';

const routes: Routes = [
  { path: '', canActivate: [isAuthenticatedGuard], component: AcademyComponent, data: { breadcrumb: 'Lista Tutorial' } },
  { path: 'tutorial/add', canActivate: [IsAdminGuard], component: TutorialAddComponent, data: { breadcrumb: 'Aggiungi Tutorial' } },
  { path: 'tutorial-details/:id', canActivate: [isAuthenticatedGuard], component: TutorialDetailsComponent, data: { breadcrumb: 'Info Tutorial' } },
  { path: 'tutorial/edit/:id', canActivate: [IsAdminGuard], component: TutorialEditComponent, data: { breadcrumb: 'Modifica il Tutorial' }},
  { path: 'category/add', canActivate: [IsAdminGuard], component: CategoriesAddComponent, data: { breadcrumb: "Aggiungi Categoria"}},
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AcademyManagerRoutingModule { }
