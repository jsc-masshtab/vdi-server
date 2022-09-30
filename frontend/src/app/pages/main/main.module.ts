import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { DashboardRoutingModule } from '@app/dashboard/dashboard-routing.module';
import { SharedModule } from '@app/shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { MainComponent } from './main.component';
import { MainService } from './main.service';

@NgModule({
  declarations: [
    MainComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    DashboardRoutingModule
  ],
  providers: [
    MainService
  ],
  exports: [
    MainComponent
  ]
})
export class MainModule { }
