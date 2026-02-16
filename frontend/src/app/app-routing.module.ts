import { NgModule, Component } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { isAuthenticatedGuard } from './guards/isAuthenticated.guard';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ProfileComponent } from './pages/profile/profile-details/profile.component';
import { LoginComponent } from './pages/auth/login/login.component';
import { DefaultComponent } from './ed-theme/templates/default/default.component';
import { FullWidthComponent } from './ed-theme/templates/full-width/full-width.component';
import { SettingsComponent } from './pages/settings/settings.component';
import { ProfileEditComponent } from './pages/profile/profile-edit/profile-edit.component';
import { UsersListComponent } from './pages/settings/user-manager/users-list/users-list.component';
import { CustomizerComponent } from './pages/settings/customizer/customizer.component';
import { RegistrationComponent } from './pages/auth/registration/registration.component';
import { ResetPasswordComponent } from './pages/auth/reset-password/reset-password.component';
import { InsertEmailComponent } from './pages/auth/insert-email/insert-email.component';
import { UserAddComponent } from './pages/settings/user-manager/user-add/user-add.component';
import { UserDetailsComponent } from './pages/settings/user-manager/user-details/user-details.component';
import { IsSuperAdminGuard } from './guards/is-super-admin.guard';
import { TutorialDetailsComponent } from './pages/academy/tutorial-details/tutorial-details.component';
import { TutorialAddComponent } from './pages/academy/tutorial-add/tutorial-add.component';
import { TutorialEditComponent } from './pages/academy/tutorial-edit/tutorial-edit.component';
import { IsAdminGuard } from './guards/is-admin.guard';
import { IsUserGuard } from './guards/is-user.guard';
import { ProjectsGeneralSchedulerComponent } from './modules/sprint-manager/projects-general-scheduler/projects-general-scheduler.component';
const routes: Routes = [
  {
    path: '',
    component: DefaultComponent,
    children: [

      // Dashboard
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', canActivate: [isAuthenticatedGuard], component: DashboardComponent },

      // Profile
      { path: 'profile', canActivate: [isAuthenticatedGuard], component: ProfileComponent, data: { breadcrumb: 'Profilo' } },
      { path: 'edit-profile', canActivate: [isAuthenticatedGuard], component: ProfileEditComponent,  data: { breadcrumb: 'Modifica Profile' } },

      // Settings 
      { path: 'settings', canActivate: [isAuthenticatedGuard], component: SettingsComponent },
      { path: 'customizer', canActivate: [IsSuperAdminGuard], component: CustomizerComponent },
      
      // Settings > User Manager
      { path: 'usermanager/users-list', canActivate: [IsSuperAdminGuard], component: UsersListComponent },
      { path: 'usermanager/user-add', canActivate: [IsSuperAdminGuard], component: UserAddComponent },
      { path: 'usermanager/user-details/:id', canActivate: [IsSuperAdminGuard], component: UserDetailsComponent },

      // Payments
      {
        path: 'payments',
        canActivate: [isAuthenticatedGuard, IsUserGuard],
        data: { breadcrumb: 'Pagamenti e Fatturazione' },
        loadChildren: () => import('./modules/payments-manager/payments-manager.module').then(m => m.PaymentsManagerModule),
      },

      // Tickets
      {
        path: 'tickets',
        canActivate: [isAuthenticatedGuard],
        data: { breadcrumb: 'Tickets' },
        loadChildren: () => import('./modules/ticket-manager/ticket-manager.module').then(m => m.TicketManagerModule),
      },
      
      // Academy
      { 
        path: 'academy', 
        canActivate: [isAuthenticatedGuard],
        data: { breadcrumb: 'Tutorial'},
        loadChildren: () => import('./pages/academy/academy-manager.module').then(m => m.AcademyManagerModule),
      },
   
      // Finance Manager
      {
        path: 'finance',
        canActivate: [isAuthenticatedGuard, IsAdminGuard],
        data: { breadcrumb: 'Gestione Finanziaria' },
        loadChildren: () => import('./modules/finance_manager/finance-manager.module').then(m => m.FinanceManagerModule),
      },

      // Project
      {
        path: 'projects/general-scheduler',
        canActivate: [isAuthenticatedGuard, IsAdminGuard],
        component: ProjectsGeneralSchedulerComponent,
        data: { breadcrumb: 'Fasi globali' },
      },
      {
        path: 'projects',
        canActivate: [isAuthenticatedGuard, IsUserGuard],
        data: { breadcrumb: 'Progetti' },
        loadChildren: () => import('./modules/project-manager/project-manager.module').then(m => m.ProjectManagerModule),
      },

      // Documents
      {
        path: 'documents',
        canActivate: [isAuthenticatedGuard, IsAdminGuard],
        data: { breadcrumb: 'Documenti' },
        loadChildren: () => import('./modules/documents/documents.module').then(m => m.DocumentsModule),
      },
    ],
  },
  {
    path: '',
    component: FullWidthComponent,
    children: [

      // Auth
      { path: 'login', component: LoginComponent },
      //{ path: 'registration', component: RegistrationComponent },
      { path: 'password-reset', component: ResetPasswordComponent },
      { path: 'insert-email', component: InsertEmailComponent },

    ],
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
