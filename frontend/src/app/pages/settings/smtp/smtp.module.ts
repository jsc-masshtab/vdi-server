import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';

import { SmtpComponent } from './smtp.component';
import { SharedModule } from '@shared/shared.module';
import { SmtpModalComponent } from './smtp-modal/smtp-modal.component';

@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    FontAwesomeModule,
    MatDialogModule,
    ReactiveFormsModule
  ],
  entryComponents: [
    SmtpModalComponent
  ],
  declarations: [SmtpComponent, SmtpModalComponent]
})
export class SmtpModule { }
