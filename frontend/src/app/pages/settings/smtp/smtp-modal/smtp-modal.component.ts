import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '@core/components/wait/wait.service';
import { ISmtpSettings, SmtpService } from '../smtp.service';


export enum Levels {
  Off = 'Отключено',
  All = 'Все сообщения',
  Warnings = 'Предупреждения и ошибки',
  Errors = 'Только ошибки',
}

@Component({
  selector: 'vdi-smtp-modal',
  templateUrl: './smtp-modal.component.html',
  styleUrls: ['./smtp-modal.component.scss']
})
export class SmtpModalComponent implements OnInit, OnDestroy {
  public smtpForm: FormGroup;
  public checkValid: boolean = false;
  public data: ISmtpSettings;
  public sub: Subscription;

  public levels = [
    {description: Levels.Off, value: 4},
    {description: Levels.All, value: 0},
    {description: Levels.Warnings, value: 1},
    {description: Levels.Errors, value: 2},
  ];

  constructor(
    private dialogRef: MatDialogRef<any>,
    private formBuilder: FormBuilder,
    private waitService: WaitService,
    private smtpService: SmtpService,
    @Inject(MAT_DIALOG_DATA) data: ISmtpSettings
  ) { 
    this.data = data;
  }
  
  ngOnInit() {
    const {hostname, port, fromAddress, user, password, level, TLS, SSL} = this.data;
    
    this.smtpForm = this.formBuilder.group({
      hostname: [hostname, [Validators.required]],
      port: [port],
      fromAddress: [fromAddress, [Validators.required, Validators.pattern(/^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/)]],
      user: [user, [Validators.required]],
      password: [password, [Validators.required]],
      level: [level],
      TLS: [TLS],
      SSL: [SSL],
    });
  }

  public onSubmit(): void {
    this.checkValid = true;

    if (this.smtpForm.status === 'VALID') {
      
      this.waitService.setWait(true);

      this.sub = this.smtpService.changeSmtpSettings(this.smtpForm.value).subscribe((res) => {

        const response = res.data.changeSmtpSettings;
        
        if (response.ok){
          this.smtpService.getSmptSettings().refetch();
          this.waitService.setWait(false);
          this.dialogRef.close()
        }
      })
    }
  }

  public close(): void {
    this.dialogRef.close();
  }

  ngOnDestroy() {
    if (this.sub){
      this.sub.unsubscribe()
    }
  }
}
