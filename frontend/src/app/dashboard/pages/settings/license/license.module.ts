import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LicenseComponent } from './license.component';
import { LicenseService } from './license.service';
import { SharedModule } from '../../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

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
