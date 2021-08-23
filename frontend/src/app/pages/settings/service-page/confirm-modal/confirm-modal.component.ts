import { Component, Inject, OnInit } from '@angular/core';
import { FormGroup, Validators, FormBuilder } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';

import { modalData } from '../service-page.component';
import { IMutationApiModel, IQueryService, ServicePageMapper } from '../service-page.mapper';
import { ServicePageService } from '../service-page.service';


@Component({
  selector: 'vdi-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent implements OnInit {

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
    if (this.confirmForm.status === 'VALID') {
       
      const params: modalData  = {
        serviceName: this.data.serviceName,
        actionType: this.data.actionType,
        ...this.confirmForm.value
      }
      console.log(params);
      
      this.waitService.setWait(true);
      this.servicePageService.updateService(params).subscribe((res) => {
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

  
  public get isPasswordEmpty(): boolean {
    return !this.confirmForm.get('password').valid && this.confirmForm.get('password').touched;
  }
  
}
