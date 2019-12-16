import { EventsComponent } from './all-events/events.component';
import { EventsService } from './all-events/events.service';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';



@NgModule({
  declarations: [
    EventsComponent
  ],
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    AppRoutingModule
  ],
  providers: [EventsService],
  exports: [
    EventsComponent
  ]
})
export class EventsModule { }

