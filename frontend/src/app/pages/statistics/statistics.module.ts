import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { StatisticsComponent } from './statistics.component';
import { SharedModule } from '@app/shared/shared.module';
import { StatisticsService } from './statistics.service';


@NgModule({
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    ReactiveFormsModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  providers: [
    StatisticsService,
  ],
  declarations: [StatisticsComponent]
})
export class StatisticsModule { }
