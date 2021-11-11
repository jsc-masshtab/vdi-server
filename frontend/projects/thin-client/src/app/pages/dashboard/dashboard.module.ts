import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { CoreModule } from '../../core/core.module';
import { PoolsModule } from '../pools/pools.module';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './dashboard.component';



@NgModule({
  declarations: [
    DashboardComponent,

  ],
  imports: [
    CommonModule,
    CoreModule,
    FontAwesomeModule,
    DashboardRoutingModule,
    HttpClientModule,
    PoolsModule
  ]
})


export class DashboardModule {
  
}
