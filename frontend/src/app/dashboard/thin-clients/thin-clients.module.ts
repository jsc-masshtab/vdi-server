import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ThinClientsComponent } from './thin-clients.component';
import { SharedModule } from '../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { ThinClientsService } from './thin-clients.service';
import { ThinClientDetailsComponent } from './thin-client-details/thin-client-details.component';
import { AppRoutingModule } from 'src/app/app-routing.module';
import { ThinClientStatisticComponent } from './thin-client-statistic/thin-client-statistic.component';
import { DisconnectThinClientComponent } from './thin-client-details/disconnect-thin-client/disconnect-thin-client.component';
import { MatDialogModule } from '@angular/material';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDialogModule,
    ReactiveFormsModule,
  ],
  declarations: [
    ThinClientsComponent,
    ThinClientDetailsComponent,
    ThinClientStatisticComponent,
    DisconnectThinClientComponent
  ],
  providers: [
    ThinClientsService
  ],
  entryComponents: [
    DisconnectThinClientComponent
  ]
})
export class ThinClientsModule { }