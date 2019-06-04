import { NodeDetailsComponent } from './resourses/nodes/node-details/node-details.component';
import { ClustersComponent } from './resourses/clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { PollsComponent } from './polls/polls.component';
import { ServersComponent } from './settings/servers/servers.component';
import { NodesComponent } from './resourses/nodes/nodes.component';
import { DatapoolsComponent } from './resourses/datapools/datapools.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'resourses/clusters',
    pathMatch: 'full'
  },
  {
    path: 'settings/controllers',
    component: ServersComponent
  },
  {
    path: 'resourses/clusters',
    component: ClustersComponent
  },
  {
    path: 'resourses/clusters/:id',
    component: ClusterDetailsComponent
  },
  {
    path: 'resourses/nodes',
    component: NodesComponent
  },
  {
    path: 'resourses/nodes/:id',
    component: NodeDetailsComponent
  },
  {
    path: 'resourses/datapools',
    component: DatapoolsComponent
  },
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
  imports: [RouterModule.forRoot(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class AppRoutingModule {}