import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { YesNoFormComponent } from './yes-no-form.component';




const DECLORATIONS = [YesNoFormComponent];

@NgModule({
  declarations: DECLORATIONS,
  exports: DECLORATIONS,
  imports: [CommonModule, FontAwesomeModule, MatDialogModule],
})
export class  YesNoFormModule {}
