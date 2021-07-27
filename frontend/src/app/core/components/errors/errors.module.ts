import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { ErrorsComponent } from './errors.component';
import { ErrorsService } from './errors.service';



@NgModule({
  declarations: [
   ErrorsComponent
  ],
  imports: [
    CommonModule,
    FontAwesomeModule
  ],
  providers: [ErrorsService],
  exports: [ErrorsComponent],
})


export class ErrorsModule {

  constructor() {
  }
}
