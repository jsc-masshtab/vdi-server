import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { WaitService } from '@core/components/wait/wait.service';
import { ISmtpSettings } from '../smtp.service';

enum Levels {
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
export class SmtpModalComponent implements OnInit {
  public smtpForm: FormGroup;
  public checkValid: boolean = false;
  public data: ISmtpSettings;

  public levels = [
    {description: 'Отключено', value: 4},
    {description: 'Все сообщения', value: 0},
    {description: 'Предупреждения и ошибки', value: 1},
    {description: 'Только ошибки', value: 2},
  ];

  constructor(
    private dialogRef: MatDialogRef<any>,
    private formBuilder: FormBuilder,
    private waitService: WaitService,
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
      user:[user, [Validators.required]],
      password: [password, [Validators.required]],
      level:[this.levels.filter(l => l.value === level)],
      TLS:[TLS],
      SSL:[SSL],
    });
  }

  public onSubmit(): void {
    console.log(this.smtpForm.value);
    this.checkValid = true;
    if (this.smtpForm.status === 'VALID') {
       
      // const params: any  = {
      //   ...this.smtpForm.value
      // }

      this.waitService.setWait(true);
      this.waitService.setWait(false);

      }
      
  }

  public close(): void {
    this.dialogRef.close();
  }

  
  public get levelDescription(): string {
    const {level} = this.data;
    switch (level) {
      case 4:
        return Levels.Off;
      case 2:
        return Levels.Errors;
      case 1:
        return Levels.Warnings;
      case 0:
        return Levels.All
      default:
        throw new Error('Something went wrong');        
    }
  }
  
}
