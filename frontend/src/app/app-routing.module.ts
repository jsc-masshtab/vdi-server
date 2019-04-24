import { ClustersComponent } from './main-vdi-cluster/clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TemplatesComponent } from './templates/templates.component';
import { PollsComponent } from './polls/polls.component';
import { ServersComponent } from './settings/servers/servers.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'resourses',
    pathMatch: 'full'
  },
  {
    path: 'settings/servers',
    component: ServersComponent
  },
  {
    path: 'nodes/:id/clusters',
    component: ClustersComponent
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
