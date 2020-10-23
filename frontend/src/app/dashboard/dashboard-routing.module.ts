import { GroupsDetailsComponent } from './settings/groups/groups-details/groups-details.component';
import { GroupsComponent } from './settings/groups/all-groups/groups.component';
import { LoginGuard } from './../login/login.guard';


import { TemplateDetailsComponent } from './resourses/templates/template-details/template-details.component';
import { DatapoolDetailsComponent } from './resourses/datapools/datapool-details/datapool-details.component';
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
import { VmDetailsComponent } from './resourses/vms/vms-details/vm-details.component';
import { EventsComponent } from './log/events/all-events/events.component';
import { DashboardComponent } from './dashboard.component';
import { AuthenticationDirectoryComponent } from './settings/auth-directory/all-auth-directory/all-auth-directory.component';
import { AuthenticationDirectoryDetailsComponent } from './settings/auth-directory/auth-directory-details/auth-directory-details.component';
import { UserDetailsComponent } from './settings/users/user-details/user-details.component';
import { ControllerDetailsComponent } from './settings/controllers/controller-details/controller-details.component';
import { LicenseComponent } from './settings/license/license.component';
import { TasksComponent } from './log/tasks/all-tasks/tasks.component';


const routes: Routes = [
  {
    path: 'pages',
    component: DashboardComponent,
    canActivate: [LoginGuard],
    canActivateChild: [LoginGuard],
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
        path: 'controllers',
        component: ControllersComponent,
        children: [
          {
            path: ':id',
            component: ControllerDetailsComponent
          }
        ]
      },
      {
        path: 'settings/license',
        component: LicenseComponent
      },
      {
        path: 'settings/users',
        component: UsersComponent,
        children: [
          {
            path: ':id',
            component: UserDetailsComponent
          }
        ]
      },
      {
        path: 'settings/groups',
        component: GroupsComponent,
        children: [
          {
            path: ':id',
            component: GroupsDetailsComponent
          }
        ]
      },
      {
        path: 'settings/auth-directory',
        component: AuthenticationDirectoryComponent,
        children: [
          {
            path: ':id',
            component: AuthenticationDirectoryDetailsComponent
          }
        ]
      },
      {
        path: 'log/events',
        component: EventsComponent
      },
      {
        path: 'log/tasks',
        component: TasksComponent
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
    ]
  },
  {
    path: '**',
    redirectTo: 'pages'
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)], // <-- debugging purposes only { enableTracing: true }
  exports: [RouterModule]
})


export class DashboardRoutingModule {}
