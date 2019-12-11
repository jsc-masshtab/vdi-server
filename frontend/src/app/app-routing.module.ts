import { LoginComponent } from './login/login.component';
import { TemplateDetailsComponent } from './resourses/templates/template-details/template-details.component';
import { DatapoolDetailsComponent } from './resourses/datapools/datapool-details/datapool-details.component';
import { PoolDetailsComponent } from './pools/pool-details/pool-details.component';
import { PoolsComponent } from './pools/all-pools/pools.component';
import { VmsComponent } from './resourses/vms/all-vms/vms.component';

import { NodeDetailsComponent } from './resourses/nodes/node-details/node-details.component';
import { ClustersComponent } from './resourses/clusters/all-clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
// import { ControllersComponent } from './settings/controllers/all-controllers/controllers.component';
import { NodesComponent } from './resourses/nodes/all-nodes/nodes.component';
import { DatapoolsComponent } from './resourses/datapools/all-datapools/datapools.component';
import { ClusterDetailsComponent } from './resourses/clusters/cluster-details/cluster-details.component';
import { TemplatesComponent } from './resourses/templates/all-templates/templates.component';
import { UsersComponent } from './settings/users/all-users/users.component';
import { VmDetailsComponent } from './resourses/vms/vms-details/vm-details.component';
import { EventsComponent } from './log/events/all-events/events.component';

// {
//   path: 'settings/controllers',
//   component: ControllersComponent
// },

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
    component: LoginComponent
  },
  {
    path: 'settings/users',
    component: UsersComponent
  },
  {
    path: 'log/events',
    component: EventsComponent
  },
  {
    path: 'resourses/clusters',
    component: ClustersComponent,
    children: [
      {
        path: ':address/:id',
        component: ClusterDetailsComponent
      }
    ]
  },
  {
    path: 'resourses/nodes',
    component: NodesComponent,
    children: [
      {
        path: ':address/:id',
        component:  NodeDetailsComponent
      }
    ]
  },
  {
    path: 'resourses/datapools',
    component: DatapoolsComponent,
    children: [
      {
        path: ':address/:id',
        component: DatapoolDetailsComponent
      }
    ]
  },
  {
    path: 'resourses/templates',
    component: TemplatesComponent,
    children: [
      {
        path: ':address/:id',
        component: TemplateDetailsComponent
      }
    ]
  },
  {
    path: 'resourses/vms',
    component: VmsComponent,
    children: [
      {
        path: ':address/:id',
        component: VmDetailsComponent
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
