import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { SharedModule } from '@app/shared/shared.module';

import { ServicePageComponent } from './service-page.component';

@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
  ],
  declarations: [ServicePageComponent]
})
export class ServicePageModule { }
