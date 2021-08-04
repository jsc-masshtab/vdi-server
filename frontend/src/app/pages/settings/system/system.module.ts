import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '@shared/shared.module';
import { SystemComponent } from './system.component';



@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
  ],
  declarations: [SystemComponent],
})

export class SystemModule { }
