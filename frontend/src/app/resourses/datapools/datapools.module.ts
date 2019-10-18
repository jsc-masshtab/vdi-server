import { DatapoolDetailsComponent } from './datapool-details/datapool-details.component';
import { DatapoolsComponent } from './all-datapools/datapools.component';
import { DatapoolsService } from './all-datapools/datapools.service';

import { AppRoutingModule } from '../../app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
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
    BrowserAnimationsModule,
    AppRoutingModule
  ],
  providers: [DatapoolsService],
  exports: [
    DatapoolsComponent,
    DatapoolDetailsComponent
  ]
})
export class DatapoolsModule { }
