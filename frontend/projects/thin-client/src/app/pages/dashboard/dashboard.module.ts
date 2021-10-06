import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { HeaderUserComponent } from '../../core/header-user/header-user.component';


import { MainMenuComponent } from '../../core/main-menu/main-menu.component';
import { WaitComponent } from '../../core/wait/wait.component';
import { PoolsModule } from '../pools/pools.module';
import { DashboardRoutingModule } from './dashboard-routing.module';
import { DashboardComponent } from './dashboard.component';



@NgModule({
  declarations: [
    DashboardComponent,
    MainMenuComponent,
    WaitComponent,
    HeaderUserComponent
  ],
  imports: [
    CommonModule,
    FontAwesomeModule,
    DashboardRoutingModule,
    HttpClientModule,
    PoolsModule
  ]
})


export class DashboardModule {
  
}
