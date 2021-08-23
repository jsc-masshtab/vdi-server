import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormGroup, Validators, FormBuilder } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';
import { Subscription } from 'rxjs';

import { modalData } from '../service-page.component';
import { IMutationApiModel, IQueryService, ServicePageMapper } from '../service-page.mapper';
import { ServicePageService } from '../service-page.service';


@Component({
  selector: 'vdi-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent implements OnInit, OnDestroy {
  private sub: Subscription;
  public checkValid: boolean = false;
  public data: modalData;
  public confirmForm: FormGroup;
  public services: IQueryService[];
  
  constructor(
    private waitService: WaitService,
    private servicePageService: ServicePageService,
    private formBuilder: FormBuilder,
    private dialogRef: MatDialogRef<ConfirmModalComponent>,
    @Inject(MAT_DIALOG_DATA) data: modalData
    ) {      
      this.data = data;
     }

  public ngOnInit(): void {
    this.confirmForm = this.formBuilder.group({
      password: ['', [Validators.required]]
    });
  }


  public close(): void {
    this.dialogRef.close();
  }

  public onSubmit(): void {
    this.checkValid = true;
    if (this.confirmForm.status === 'VALID') {
       
      const params: modalData  = {
        serviceName: this.data.serviceName,
        actionType: this.data.actionType,
        ...this.confirmForm.value
      }

      this.waitService.setWait(true);
      this.sub = this.servicePageService.updateService(params).subscribe((res) => {
        const response: IMutationApiModel = res.data.doServiceAction;
        const mapper = new ServicePageMapper();
        const serviceInfo = mapper.serverMutationModelToClientModel(response)
        if (serviceInfo.ok && !!serviceInfo.status ){
            this.servicePageService.getServicesInfo().refetch();
            this.waitService.setWait(false);
            this.dialogRef.close()
          }
        })
      }
  }

  ngOnDestroy() {
    this.sub.unsubscribe()
  }
}
