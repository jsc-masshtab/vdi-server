import { PoolDetailsComponent } from './pools/pool-details/pool-details.component';
import { PoolsComponent } from './pools/all-pools/pools.component';
import { VmsComponent } from './resourses/vms/all-vms/vms.component';

import { NodeDetailsComponent } from './resourses/nodes/node-details/node-details.component';
import { ClustersComponent } from './resourses/clusters/all-clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ControllersComponent } from './settings/controllers/all-controllers/controllers.component';
import { NodesComponent } from './resourses/nodes/all-nodes/nodes.component';
import { DatapoolsComponent } from './resourses/datapools/all-datapools/datapools.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';
import { TemplatesComponent } from './resourses/templates/all-templates/templates.component';
import { UsersComponent } from './settings/users/all-users/users.component';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'pools',
    pathMatch: 'full'
  },
  {
    path: 'pools',
    component: PoolsComponent,
    children: [
      {
        path: ':type/:id',
        component: PoolDetailsComponent
      }
    ]
  },
  {
    path: 'settings/controllers',
    component: ControllersComponent
  },
  {
    path: 'settings/users',
    component: UsersComponent
  },
  {
    path: 'resourses/clusters',
    component: ClustersComponent,
    children: [
      {
        path: ':id',
        component: ClusterDetailsComponent
      }
    ]
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
    path: 'resourses/templates',
    component: TemplatesComponent
  },
  {
    path: 'resourses/vms',
    component: VmsComponent
  },
  {
    path: '**',
    redirectTo: 'pools'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class AppRoutingModule {}