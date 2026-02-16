import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ProfileComponent } from './pages/profile/profile-details/profile.component';
import { HeaderComponent } from './ed-theme/parts/header/header.component';
import { FooterComponent } from './ed-theme/parts/footer/footer.component';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatMenuModule } from '@angular/material/menu';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatTabsModule } from '@angular/material/tabs';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatCardModule } from '@angular/material/card';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations'
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { APP_BASE_HREF, HashLocationStrategy, LocationStrategy, registerLocaleData } from '@angular/common';
import { isAuthenticatedGuard } from './guards/isAuthenticated.guard';
import { AuthService } from './services/auth/auth.service';
import { SidenavComponent } from './ed-theme/parts/sidenav/sidenav.component';
import { SublevelMenuComponent } from './ed-theme/parts/sidenav/sublevel-menu.component';
import { BodyComponent } from './ed-theme/parts/body/body.component';
import { CookieService } from 'ngx-cookie-service';
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { LoginComponent } from './pages/auth/login/login.component';
import { PermissionService } from './services/auth/permission.service';
import { BodyFullWidthComponent } from './ed-theme/parts/body-full-width/body-full-width.component';
import { FullWidthComponent } from './ed-theme/templates/full-width/full-width.component';
import { DefaultComponent } from './ed-theme/templates/default/default.component';
import { ApiService } from './services/api/api.services';
import { AuthInterceptor } from './interceptors/auth.interceptor';
import { SettingsComponent } from './pages/settings/settings.component';
import { RegistrationComponent } from './pages/auth/registration/registration.component';
import { JWTUtils } from './util/jwt_validator';
import { ProfileEditComponent } from './pages/profile/profile-edit/profile-edit.component';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { UsersListComponent } from './pages/settings/user-manager/users-list/users-list.component';
import { CustomizerComponent } from './pages/settings/customizer/customizer.component';
import { MatTableModule } from '@angular/material/table';
import { UserDetailsComponent } from './pages/settings/user-manager/user-details/user-details.component';
import { UserAddComponent } from './pages/settings/user-manager/user-add/user-add.component';
import { MatDialogModule } from '@angular/material/dialog';
import { InsertEmailComponent } from './pages/auth/insert-email/insert-email.component';
import { TicketListAdminComponent } from './modules/ticket-manager/ticket-list-admin/ticket-list-admin.component';
import { TicketAddComponent } from './modules/ticket-manager/ticket-add/ticket-add.component';
import { TicketDetailsComponent } from './modules/ticket-manager/ticket-details/ticket-details.component';
import { TicketApiService } from './services/api/ticket-api.services';
import { SprintApiService } from './services/api/sprint-api.service';
import { ReportApiService } from './services/api/report-api.service';
import { TutorialApiService } from './services/api/academy-api.services';
import { AcademyComponent } from './pages/academy/academy/academy.component';
import { PaymentsComponent } from './modules/payments-manager/payments.component';
import { DateParser } from './util/date_parse';
import { PaymentsApiService } from './services/api/payments-api.services';
import { MatProgressBarModule } from "@angular/material/progress-bar";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";
import { TutorialDetailsComponent } from "./pages/academy/tutorial-details/tutorial-details.component";
import { MatGridListModule } from "@angular/material/grid-list";
import { SubscriptionDetailComponent } from "./modules/payments-manager/subscriptions/subscription-detail/subscription-detail.component";
import { PaymentDetailComponent } from "./modules/payments-manager/payments/payment-detail/payment-detail.component";
import { NZ_I18N } from 'ng-zorro-antd/i18n';
import { it_IT } from 'ng-zorro-antd/i18n';
import it from '@angular/common/locales/it';
import { IconsProviderModule } from './icons-provider.module';
import { NzLayoutModule } from 'ng-zorro-antd/layout';
import { NzMenuModule } from 'ng-zorro-antd/menu';
import { NzListModule } from "ng-zorro-antd/list";
import { NzCommentModule } from "ng-zorro-antd/comment";
import { NzAvatarModule } from "ng-zorro-antd/avatar";
import { NzFormModule } from "ng-zorro-antd/form";
import { NzButtonModule } from "ng-zorro-antd/button";
import { NzInputModule } from "ng-zorro-antd/input";
import {AvatarModule} from "./pages/profile/avatar/avatar.module";
import { DragDropModule } from '@angular/cdk/drag-drop';
import { TicketEditComponent } from './modules/ticket-manager/ticket-edit/ticket-edit.component';
import { MatChipsModule } from '@angular/material/chips';
import { ProjectApiService } from './services/api/project-api.services';
import { ProjectListComponent } from './modules/project-manager/project-list/project-list.component';
import { ProjectAddComponent } from './modules/project-manager/project-add/project-add.component';
import { ProjectEditComponent } from './modules/project-manager/project-edit/project-edit.component';
import { ProjectDetailsComponent } from './modules/project-manager/project-details/project-details.component';
import { MatPaginatorModule } from '@angular/material/paginator';
import { TutorialAddComponent } from './pages/academy/tutorial-add/tutorial-add.component';
import { TutorialEditComponent } from './pages/academy/tutorial-edit/tutorial-edit.component';
import { MatSortModule } from '@angular/material/sort';
import { BreadcrumbsComponent } from './ed-theme/parts/breadcrumbs/breadcrumbs/breadcrumbs.component';
import { SimpleCardComponent } from './ed-theme/elements/cards/simple-card/simple-card.component';
import { CategoriesAddComponent } from './pages/academy/categories-add/categories-add.component';
import { TicketsByPeriodComponent } from './modules/ticket-manager/tickets-by-period/tickets-by-period.component';
import { TicketListComponent } from './modules/ticket-manager/ticket-list/ticket-list.component';
import { ProjectsGeneralScheduleComponent } from './modules/project-manager/projects-general-schedule/projects-general-schedule.component';
import { ProjectsGeneralSchedulerComponent } from './modules/sprint-manager/projects-general-scheduler/projects-general-scheduler.component';
import { SharedModule } from './shared/shared.module';
import { WorkspaceInterceptor } from './interceptors/workspace.interceptor';

registerLocaleData(it);

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    ProfileComponent,
    HeaderComponent,
    FooterComponent,
    BodyComponent,
    SidenavComponent,
    SublevelMenuComponent,
    LoginComponent,
    BodyFullWidthComponent,
    FullWidthComponent,
    DefaultComponent,
    SettingsComponent,
    RegistrationComponent,
    ProfileEditComponent,
    UsersListComponent,
    CustomizerComponent,
    UserDetailsComponent,
    UserAddComponent,
    InsertEmailComponent,
    TicketListAdminComponent,
    TicketListComponent,
    TicketAddComponent,
    TicketDetailsComponent,
    AcademyComponent,
    TutorialDetailsComponent,
    PaymentsComponent,
    SubscriptionDetailComponent,
    PaymentDetailComponent,
    TicketEditComponent,
    ProjectListComponent,
    ProjectAddComponent,
    ProjectEditComponent,
    ProjectDetailsComponent,
    TutorialAddComponent,
    TutorialEditComponent,
    BreadcrumbsComponent,
    SimpleCardComponent,
    CategoriesAddComponent,
    TicketsByPeriodComponent,
    ProjectsGeneralScheduleComponent,
    ProjectsGeneralSchedulerComponent,
],
    imports: [
        BrowserModule.withServerTransition({appId: 'serverApp'}),
        BrowserAnimationsModule,
        FormsModule,
        ReactiveFormsModule,
        MatButtonModule,
        MatSidenavModule,
        MatMenuModule,
        MatToolbarModule,
        MatIconModule,
        MatDialogModule,
        MatTableModule,
        MatListModule,
        MatTabsModule,
        MatCardModule,
        MatSnackBarModule,
        MatExpansionModule,
        MatTooltipModule,
        AppRoutingModule,
        HttpClientModule,
        MatProgressBarModule,
        MatGridListModule,
        IconsProviderModule,
        NzLayoutModule,
        NzMenuModule,
        NzListModule,
        NzCommentModule,
        NzAvatarModule,
        NzFormModule,
        NzButtonModule,
        NzInputModule,
        AvatarModule,
        MatChipsModule,
        MatPaginatorModule,
        MatSortModule,
        DragDropModule,
        MatProgressSpinnerModule,
        SharedModule,
        
    ],
  providers: [
    AuthService,
    isAuthenticatedGuard,
    CookieService,
    PermissionService,
    ApiService,
    TicketApiService,
    TutorialApiService,
    PaymentsApiService,
    JWTUtils,
    DateParser,
    SidenavComponent,
    ProjectApiService,
    SprintApiService,
    ReportApiService,
    /*{ 
      provide: LocationStrategy, 
      useClass: PathLocationStrategy 
    },*/
    {provide: LocationStrategy, useClass: HashLocationStrategy},
    { 
      provide: APP_BASE_HREF, 
      useValue: '/' 
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: WorkspaceInterceptor,
      multi: true
    },
    { provide: NZ_I18N, useValue: it_IT },
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
