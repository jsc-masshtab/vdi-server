import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { WaitService } from '@app/core/components/wait/wait.service';
import { ApolloQueryResult } from 'apollo-client';
import { Subscription } from 'rxjs';

import { SmtpModalComponent } from './smtp-modal/smtp-modal.component';
import { ISmtpResponse, ISmtpSettings, SmtpService } from './smtp.service';



@Component({
  selector: 'vdi-smtp',
  templateUrl: './smtp.component.html',
  styleUrls: ['./smtp.component.scss']
})
export class SmtpComponent implements OnInit {

  public sub: Subscription;
  public smtpSettings: ISmtpSettings;

  public readonly intoCollection: ReadonlyArray<object> = [
    {
      title: 'Адрес сервера',
      type: 'string',
      property: 'hostname'
    },
    {
      title: 'Порт',
      type: 'string',
      property: 'port'
    },
    {
      title: 'Имя пользователя',
      type: 'string',
      property: 'user'
    },
    {
      title: 'E-mail отправителя',
      type: 'string',
      property: 'fromAddress'
    },
    {
      title: 'Уровень информирования',
      type: 'level',
      property: 'level'
    },
    {
      title: 'TLS',
      type: 'boolean',
      property: 'TLS'
    },
    {
      title: 'SSL',
      type: 'boolean',
      property: 'SSL'
    }
  ]

  constructor(
    private smtpService: SmtpService,
    private dialog: MatDialog,
    private waitService: WaitService) { }

  ngOnInit() {
    this.getSmtpSettings()
  }

  public getSmtpSettings(): void {
    this.smtpService.getSmptSettings().valueChanges.subscribe((res: ApolloQueryResult<ISmtpResponse>) => {
      this.smtpSettings = res.data.smtpSettings;
     
   });
  }
  
  public openModal(): void  {
    this.dialog.open(SmtpModalComponent, {
      disableClose: true,
      width: '500px',
      data: {
       ...this.smtpSettings 
      }
    });
  }

  public reset(): void{
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
        }
      })
  }
 
  
}
