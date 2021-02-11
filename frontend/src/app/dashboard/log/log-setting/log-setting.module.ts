import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LogSettingComponent } from './log-setting.component';
import { SharedModule } from '../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AppRoutingModule } from 'src/app/app-routing.module';
import {
  MatDatepickerModule,
  MatNativeDateModule,
  MatDialogModule,
  MatSelectModule,
  MatCheckboxModule
} from '@angular/material';
import {
  FormsModule,
  ReactiveFormsModule
} from '@angular/forms';
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
