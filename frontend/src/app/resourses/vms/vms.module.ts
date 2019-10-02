

import { AppRoutingModule } from '../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from '../../common/components/shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VmsComponent } from './all-vms/vms.component';
import { VmsService } from './all-vms/vms.service';


@NgModule({
  declarations: [
    VmsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    BrowserAnimationsModule,
    AppRoutingModule
  ],
  providers: [VmsService],
  exports: [
    VmsComponent
  ]
})
export class VmsModule { }
