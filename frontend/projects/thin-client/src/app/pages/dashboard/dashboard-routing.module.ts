import { NgModule } from '@angular/core';

import { Routes, RouterModule } from '@angular/router';

import { LoginGuard } from '../../core/services/login.guard';
import { PoolsComponent } from '../pools/all-pools/pools.component';
import { PoolDetailsComponent } from '../pools/pool-details/pool-details.component';



import { DashboardComponent } from './dashboard.component';




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
            path: ':id',
            component: PoolDetailsComponent
          }
        ]
      },
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
