import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates/templates.component';
import { PollsComponent } from './polls/polls.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'resources',
    pathMatch: 'full'
  },
  {
    path: 'resourses',
    component: TemplatesComponent
  },
  {
    path: 'pools',
    component: PollsComponent
  },
  {
    path: '**',
    redirectTo: 'resources'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})


export class AppRoutingModule { }
