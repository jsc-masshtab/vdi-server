import { DatapoolDetailsComponent } from './datapool-details/datapool-details.component';
import { DatapoolsComponent } from './all-datapools/datapools.component';
import { DatapoolsService } from './all-datapools/datapools.service';

import { AppRoutingModule } from '../../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VmsModule } from '../vms/vms.module';
import { TemplatesModule } from '../templates/templates.module';

@NgModule({
  declarations: [
   DatapoolsComponent,
   DatapoolDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    VmsModule,
    TemplatesModule
  ],
  providers: [DatapoolsService],
  exports: [
    DatapoolsComponent,
    DatapoolDetailsComponent
  ]
})
export class DatapoolsModule { }
