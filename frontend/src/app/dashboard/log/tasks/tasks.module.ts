import { TasksComponent } from './all-tasks/tasks.component';
import { TasksService } from './all-tasks/tasks.service';
import { AppRoutingModule } from '../../../app-routing.module';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InfoTaskComponent } from './info-tasks/info-tasks.component';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule, MatSelectModule, MatCheckboxModule, MatDialogModule } from '@angular/material';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { library } from '@fortawesome/fontawesome-svg-core';
import { faTimesCircle } from '@fortawesome/free-solid-svg-icons';

@NgModule({
  declarations: [
    TasksComponent,
    InfoTaskComponent
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
  providers: [TasksService],
  entryComponents: [
    InfoTaskComponent
  ],
  exports: [
    TasksComponent
  ]
})
export class TasksModule {
  constructor() {
    library.add(faTimesCircle);
  }
}

