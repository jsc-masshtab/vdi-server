import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialogModule } from '@angular/material/dialog';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AppRoutingModule } from 'src/app/app-routing.module';

import { SharedModule } from '../../shared/shared.module';
import { DisconnectThinClientComponent } from './thin-client-details/disconnect-thin-client/disconnect-thin-client.component';
import { ThinClientDetailsComponent } from './thin-client-details/thin-client-details.component';
import { ThinClientStatisticComponent } from './thin-client-statistic/thin-client-statistic.component';
import { ThinClientsComponent } from './thin-clients.component';
import { ThinClientsService } from './thin-clients.service';




@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    ReactiveFormsModule,
    MatCheckboxModule
  ],
  declarations: [
    ThinClientsComponent,
    ThinClientDetailsComponent,
    ThinClientStatisticComponent,
    DisconnectThinClientComponent
  ],
  providers: [
    ThinClientsService
  ]
})
export class ThinClientsModule { }
