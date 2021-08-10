import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import {
  FormsModule,
  ReactiveFormsModule
} from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AppRoutingModule } from 'app/app-routing.module';

import { SharedModule } from '@shared/shared.module';

import { LogSettingComponent } from './log-setting.component';
import { LogSettingService } from './log-setting.service';

@NgModule({
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
    LogSettingService
  ],
  declarations: [LogSettingComponent]
})
export class LogSettingModule { }
