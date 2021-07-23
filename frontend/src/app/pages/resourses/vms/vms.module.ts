

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VmsComponent } from './all-vms/vms.component';
import { VmsService } from './all-vms/vms.service';
import { VmDetailsComponent } from './vms-details/vm-details.component';


@NgModule({
  declarations: [
    VmsComponent,
    VmDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule
  ],
  providers: [VmsService],
  exports: [
    VmsComponent,
    VmDetailsComponent
  ]
})
export class VmsModule { }
