
import { LoginComponent } from './login/login.component';
import { TemplateDetailsComponent } from './dashboard/resourses/templates/template-details/template-details.component';
import { DatapoolDetailsComponent } from './dashboard/resourses/datapools/datapool-details/datapool-details.component';
import { PoolDetailsComponent } from './dashboard/pools/pool-details/pool-details.component';
import { PoolsComponent } from './dashboard/pools/all-pools/pools.component';
import { VmsComponent } from './dashboard/resourses/vms/all-vms/vms.component';

import { NodeDetailsComponent } from './dashboard/resourses/nodes/node-details/node-details.component';
import { ClustersComponent } from './dashboard/resourses/clusters/all-clusters/clusters.component';
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { ControllersComponent } from './dashboard/settings/controllers/all-controllers/controllers.component';
import { NodesComponent } from './dashboard/resourses/nodes/all-nodes/nodes.component';
import { DatapoolsComponent } from './dashboard/resourses/datapools/all-datapools/datapools.component';
import { ClusterDetailsComponent } from './dashboard/resourses/clusters/cluster-details/cluster-details.component';
import { TemplatesComponent } from './dashboard/resourses/templates/all-templates/templates.component';
import { UsersComponent } from './dashboard/settings/users/all-users/users.component';
import { VmDetailsComponent } from './dashboard/resourses/vms/vms-details/vm-details.component';
import { EventsComponent } from './dashboard/log/events/all-events/events.component';
import { DashboardComponent } from './dashboard/dashboard.component';


const routes: Routes = [
  {
    path: 'auth',
    component: LoginComponent
  },
  {
    path: 'pages',
    component: DashboardComponent,
    children: [
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
    ]
  },
  {
    path: '**',
    redirectTo: 'pages/pools'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class AppRoutingModule {}
