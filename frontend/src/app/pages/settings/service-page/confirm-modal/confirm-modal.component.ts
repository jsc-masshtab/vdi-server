import { Component, Inject, OnInit } from '@angular/core';
import { FormGroup, Validators, FormBuilder } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { modalData } from '../service-page.component';
import { IMutationApiModel, ServicePageMapper } from '../service-page.mapper';
import { ServicePageService } from '../service-page.service';

type error = {
  message: null | string
}

@Component({
  selector: 'vdi-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent implements OnInit {
  public error: error = {
    message: null
  }
  public data: modalData;
  public confirmForm: FormGroup;

  constructor(
    private servicePageService: ServicePageService,
    private formBuilder: FormBuilder,
    private dialogRef: MatDialogRef<ConfirmModalComponent>,
    @Inject(MAT_DIALOG_DATA) data: modalData
    ) {      
      this.data = data;
     }

  public ngOnInit(): void {
    this.confirmForm = this.formBuilder.group({
      serviceName: [{value: this.data.serviceName, disabled: true}, [Validators.required]],
      actionType: [{value: this.data.actionType, disabled: true}, [Validators.required]],
      password: ['', [Validators.required]]
    });
  }


  public close(): void {
    this.dialogRef.close();
  }

  public onSubmit(): void {    
    const params: modalData  = {
      serviceName: this.data.serviceName,
      actionType: this.data.actionType,
      password: this.confirmForm.get('password').value
    }

    this.servicePageService.updateService(params).subscribe((res) => {
      const response: IMutationApiModel = res.data.doServiceAction;
      const mapper = new ServicePageMapper();
      const serviceInfo = mapper.serverMutationModelToClientModel(response)
      this.dialogRef.close(serviceInfo)
      
      }, (err: error) => {
        this.error = err
      })

  }

  
  public get isPasswordEmpty(): boolean {
    return !this.confirmForm.get('password').valid && this.confirmForm.get('password').touched;
  }
  
}
