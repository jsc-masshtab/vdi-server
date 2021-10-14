import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

import { ButtonRefreshComponent } from './button-refresh.component';




const DECLORATIONS = [ButtonRefreshComponent];

@NgModule({
  declarations: DECLORATIONS,
  exports: DECLORATIONS,
  imports: [CommonModule, FontAwesomeModule],
})
export class ButtonRefreshModule {}
