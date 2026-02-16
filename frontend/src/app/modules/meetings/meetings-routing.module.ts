import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { isAuthenticatedGuard } from 'src/app/guards/isAuthenticated.guard';
import { MeetingsListComponent } from './meetings-list/meetings-list.component';

const routes: Routes = [
  { path: '', canActivate: [isAuthenticatedGuard], component: MeetingsListComponent, data: { breadcrumb: 'Meeting List' }},
  
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class MeetingsRoutingModule { }
