import { Component, Inject, OnDestroy } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '@core/components/wait/wait.service';
import { modalData } from '../service-page.component';
import { IQueryService, ServicePageService } from '../service-page.service';


@Component({
  selector: 'vdi-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent implements OnDestroy {
  private sub: Subscription;
  public data: modalData;
  public services: IQueryService[];
  
  constructor(
    private waitService: WaitService,
    private servicePageService: ServicePageService,
    private dialogRef: MatDialogRef<ConfirmModalComponent>,
    @Inject(MAT_DIALOG_DATA) data: modalData
    ) {      
      this.data = data;
     }

  public close(): void {
    this.dialogRef.close();
  }

  public onSubmit(): void {
       
      const params: modalData  = {
        serviceName: this.data.serviceName,
        actionType: this.data.actionType,
      }

      this.waitService.setWait(true);
      this.sub = this.servicePageService.updateService(params).subscribe((res) => {
        const serviceInfo = res.data.doServiceAction;
        if (serviceInfo.ok && !!serviceInfo.serviceStatus ){
            this.servicePageService.getServicesInfo().refetch();
            this.waitService.setWait(false);
            this.dialogRef.close()
          }
        })
  }

  ngOnDestroy() {
    if (this.sub){
      this.sub.unsubscribe()
    }
  }
}
