import { ClustersComponent } from './clusters/clusters.component';
import { NodesComponent } from './nodes/nodes.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates/templates.component';
import { PollsComponent } from './polls/polls.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'resourses',
    pathMatch: 'full'
  },
  {
    path: 'nodes',
    component: NodesComponent,
    children: [
      {
        path: ':id/clusters',
        component: ClustersComponent
      }
    ]
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
    redirectTo: 'resourses'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})


export class AppRoutingModule { }
