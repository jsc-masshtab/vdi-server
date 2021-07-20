import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LogSettingComponent } from './log-setting.component';
import { SharedModule } from '../../../common/shared.module';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { AppRoutingModule } from 'src/app/app-routing.module';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSelectModule } from '@angular/material/select';
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
