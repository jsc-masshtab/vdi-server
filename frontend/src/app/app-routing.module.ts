import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates/templates.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'page',
    pathMatch: 'full'
  },
  {
    path: 'page',
    component: TemplatesComponent
  },
  {
    path: '**',
    redirectTo: 'page'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})


export class AppRoutingModule { }
