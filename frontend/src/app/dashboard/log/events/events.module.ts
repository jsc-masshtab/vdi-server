import { EventsComponent } from './all-events/events.component';
import { EventsService } from './all-events/events.service';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InfoEventComponent } from './info-event/info-event.component';



@NgModule({
  declarations: [
    EventsComponent,
    InfoEventComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule
  ],
  providers: [EventsService],
  entryComponents: [
    InfoEventComponent
  ],
  exports: [
    EventsComponent
  ]
})
export class EventsModule { }

