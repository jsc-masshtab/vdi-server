import { Component, OnDestroy } from '@angular/core';

import { MatDialogRef } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '@core/components/wait/wait.service';
import { SmtpService } from '../smtp.service';




@Component({
  selector: 'vdi-smtp-confirm-modal',
  templateUrl: './confirm-modal.component.html'
})
export class SmtpConfirmModalComponent implements OnDestroy {
  private sub: Subscription;
 
  constructor(
    private waitService: WaitService,
    private dialogRef: MatDialogRef<any>,
    private smtpService: SmtpService,
    ) {      
     
     }

  public close(): void {
    this.dialogRef.close();
  }

  public onSubmit(): void {
    const params = {
      hostname: '',
      port: 25,
      SSL: false,
      TLS: false,
      fromAddress: '',
      user: '',
      password: '',
      level: 4
    }
    this.waitService.setWait(true);
    this.sub = this.smtpService.changeSmtpSettings(params).subscribe((res) => {
      const response = res.data.changeSmtpSettings;
      
      if (response.ok){
          this.smtpService.getSmptSettings().refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      })
    }

  ngOnDestroy() {
    if (this.sub){
      this.sub.unsubscribe()
    }
  }
}
