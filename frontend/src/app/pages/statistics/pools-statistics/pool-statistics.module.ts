import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatNativeDateModule } from '@angular/material/core';

import { SharedModule } from '@app/shared/shared.module';
import { PoolsStatisticsComponent } from './pools-statistics.component';
import { PoolStatisticsService } from './pool-statistics.service';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { NgChartsModule } from 'ng2-charts';

@NgModule({
  imports: [
    SharedModule,
    CommonModule,
    FontAwesomeModule,
    ReactiveFormsModule,
    FormsModule,
    MatFormFieldModule,
    MatNativeDateModule,
    MatDatepickerModule,
    MatInputModule,
    MatSelectModule,
    NgChartsModule
  ],
  providers: [
    PoolStatisticsService
  ],
  declarations: [PoolsStatisticsComponent]
})
export class PoolStatisticsModule { }
