import { EventsComponent } from './all-events/events.component';
import { EventsService } from './all-events/events.service';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InfoEventComponent } from './info-event/info-event.component';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule, MatSelectModule, MatCheckboxModule, MatDialogModule } from '@angular/material';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { library } from '@fortawesome/fontawesome-svg-core';
import { faTimesCircle } from '@fortawesome/free-solid-svg-icons';
import { AddExportComponent } from './add-exports/add-exports.component';

@NgModule({
  declarations: [
    EventsComponent,
    InfoEventComponent,
    AddExportComponent
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
  providers: [EventsService],
  entryComponents: [
    InfoEventComponent,
    AddExportComponent
  ],
  exports: [
    EventsComponent
  ]
})
export class EventsModule {
  constructor() {
    library.add(faTimesCircle);
  }
}

