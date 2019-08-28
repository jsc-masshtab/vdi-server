import { VmsComponent } from './resourses/vms/vms.component';
import { PoolDetailsComponent } from './polls/pool-details/pool-details.component';
import { PoolsComponent } from './polls/pools.component';
import { NodeDetailsComponent } from './resourses/nodes/node-details/node-details.component';
import { ClustersComponent } from './resourses/clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ControllersComponent } from './settings/controllers/controllers.component';
import { NodesComponent } from './resourses/nodes/nodes.component';
import { DatapoolsComponent } from './resourses/datapools/datapools.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';
import { TemplatesComponent } from './resourses/templates/templates.component';
import { UsersComponent } from './settings/users/users.component';

const routes: Routes = [
  {
    path:'',
    redirectTo: 'pools',
    pathMatch: 'full'
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
    path: '**',
    redirectTo: 'pools'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class AppRoutingModule {}