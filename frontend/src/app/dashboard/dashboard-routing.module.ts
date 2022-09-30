import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ControllersComponent } from '@pages/controllers/all-controllers/controllers.component';
import { ControllerDetailsComponent } from '@pages/controllers/controller-details/controller-details.component';
import { EventsComponent } from '@pages/log/events/all-events/events.component';
import { LogSettingComponent } from '@pages/log/log-setting/log-setting.component';
import { TasksComponent } from '@pages/log/tasks/all-tasks/tasks.component';
import { VeilEventsComponent } from '@pages/log/veil-events/veil-all-events/events.component';
import { LoginGuard } from '@pages/login/login.guard';
import { PoolsComponent } from '@pages/pools/all-pools/pools.component';
import { PoolDetailsComponent } from '@pages/pools/pool-details/pool-details.component';
import { ClustersComponent } from '@pages/resourses/clusters/all-clusters/clusters.component';
import { ClusterDetailsComponent } from '@pages/resourses/clusters/cluster-details/cluster-details.component';
import { DatapoolsComponent } from '@pages/resourses/datapools/all-datapools/datapools.component';
import { DatapoolDetailsComponent } from '@pages/resourses/datapools/datapool-details/datapool-details.component';
import { NodesComponent } from '@pages/resourses/nodes/all-nodes/nodes.component';
import { NodeDetailsComponent } from '@pages/resourses/nodes/node-details/node-details.component';
import { ResourcePoolsComponent } from '@pages/resourses/resource_pools/all-resource_pools/resource_pools.component';
import { ResourcePoolDetailsComponent } from '@pages/resourses/resource_pools/resource_pool-details/resource_pool-details.component';
import { TemplatesComponent } from '@pages/resourses/templates/all-templates/templates.component';
import { TemplateDetailsComponent } from '@pages/resourses/templates/template-details/template-details.component';
import { VmsComponent } from '@pages/resourses/vms/all-vms/vms.component';
import { VmDetailsComponent } from '@pages/resourses/vms/vms-details/vm-details.component';
import { AuthenticationDirectoryComponent } from '@pages/settings/auth-directory/all-auth-directory/all-auth-directory.component';
import { AuthenticationDirectoryDetailsComponent } from '@pages/settings/auth-directory/auth-directory-details/auth-directory-details.component';
import { GroupsComponent } from '@pages/settings/groups/all-groups/groups.component';
import { GroupsDetailsComponent } from '@pages/settings/groups/groups-details/groups-details.component';
import { LicenseComponent } from '@pages/settings/license/license.component';
import { SystemComponent } from '@pages/settings/system/system.component';
import { ServicePageComponent } from '@pages/settings/service-page/service-page.component';
import { UsersComponent } from '@pages/settings/users/all-users/users.component';
import { UserDetailsComponent } from '@pages/settings/users/user-details/user-details.component';
import { ThinClientDetailsComponent } from '@pages/thin-clients/thin-client-details/thin-client-details.component';
import { ThinClientsComponent } from '@pages/thin-clients/thin-clients.component';
import { DashboardComponent } from './dashboard.component';
import { SmtpComponent } from '@pages/settings/smtp/smtp.component';
import { CacheComponent } from '@pages/settings/cache/cache.component';
import { StatisticsComponent } from '@pages/statistics/statistics.component';
import { PoolsStatisticsComponent } from '@app/pages/statistics/pools-statistics/pools-statistics.component';
import { MainComponent } from '@app/pages/main/main.component';


const routes: Routes = [
  {
    path: 'pages',
    component: DashboardComponent,
    canActivate: [LoginGuard],
    canActivateChild: [LoginGuard],
    children: [
      {
        path: '',
        redirectTo: 'main',
        pathMatch: 'full'
      },
      {
        path: 'main',
        component: MainComponent
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
        path: 'clients/session',
        component: ThinClientsComponent,
        children: [
          {
            path: ':id',
            component: ThinClientDetailsComponent
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
        path: 'settings/system',
        component: SystemComponent
      },
      {
        path: 'settings/services',
        component: ServicePageComponent
      },
      {
        path: 'settings/cache',
        component: CacheComponent
      },
      {
        path: 'settings/smtp',
        component: SmtpComponent
      },
      {
        path: 'log/events',
        component: EventsComponent
      },
      {
        path: 'log/veil-events',
        component: VeilEventsComponent
      },
      {
        path: 'log/tasks',
        component: TasksComponent
      },
      {
        path: 'log/setting',
        component: LogSettingComponent
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
        path: 'resourses/resource_pools',
        component: ResourcePoolsComponent,
        children: [
          {
            path: ':address/:id',
            component: ResourcePoolDetailsComponent
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
        path: 'statistics/statistics-web',
        component: StatisticsComponent
      },
      {
        path: 'statistics/statistics-pool',
        component: PoolsStatisticsComponent
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
