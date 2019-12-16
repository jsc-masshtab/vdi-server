import { DatapoolDetailsComponent } from './datapool-details/datapool-details.component';
import { DatapoolsComponent } from './all-datapools/datapools.component';
import { DatapoolsService } from './all-datapools/datapools.service';

import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';



@NgModule({
  declarations: [
   DatapoolsComponent,
   DatapoolDetailsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule
  ],
  providers: [DatapoolsService],
  exports: [
    DatapoolsComponent,
    DatapoolDetailsComponent
  ]
})
export class DatapoolsModule { }
