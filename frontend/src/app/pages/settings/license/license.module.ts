import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '../../../shared/shared.module';
import { LicenseComponent } from './license.component';
import { LicenseService } from './license.service';


@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
  ],
  declarations: [LicenseComponent],
  providers: [ LicenseService ]
})
export class LicenseModule { }
