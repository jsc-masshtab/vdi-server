import { VeilEventsComponent } from './veil-all-events/events.component';
import { VeilEventsService } from './veil-all-events/events.service';
import { AppRoutingModule } from '../../../../app-routing.module';
import { SharedModule } from '../../../shared/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { VeilInfoEventComponent } from './veil-info-event/info-event.component';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { library } from '@fortawesome/fontawesome-svg-core';
import { faTimesCircle } from '@fortawesome/free-solid-svg-icons';

@NgModule({
  declarations: [
    VeilEventsComponent,
    VeilInfoEventComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule,
    MatDatepickerModule,
    MatNativeDateModule,
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatSelectModule,
    MatCheckboxModule
  ],
  providers: [
    VeilEventsService
  ],
  exports: [
    VeilEventsComponent
  ]
})
export class VeilEventsModule {
  constructor() {
    library.add(faTimesCircle);
  }
}

