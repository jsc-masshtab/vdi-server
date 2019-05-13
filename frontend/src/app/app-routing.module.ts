import { ClustersComponent } from './resourses/clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates/templates.component';
import { PollsComponent } from './polls/polls.component';
import { ServersComponent } from './settings/servers/servers.component';
import { NodesComponent } from './resourses/nodes/nodes.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'resourses/clusters',
    pathMatch: 'full'
  },
  {
    path: 'settings/servers',
    component: ServersComponent
  },
  {
    path: 'resourses/clusters',
    component: ClustersComponent
  },
  {
    path: 'resourses/clusters/:id/nodes',
    component: NodesComponent
  },
  // {
  //   path: 'resourses',
  //   component: TemplatesComponent
  // },
  {
    path: 'pools',
    component: PollsComponent
  },
  {
    path: '**',
    redirectTo: 'resourses/clusters'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})


export class AppRoutingModule { }
