import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ApolloQueryResult } from 'apollo-client';

import { WaitService } from '@core/components/wait/wait.service';

import { ConfirmModalComponent } from './confirm-modal/confirm-modal.component';
import { IQueryApiModel, IQueryResponse, IQueryService, MutationServiceInfo, ServicePageMapper } from './service-page.mapper';
import { ServicePageService } from './service-page.service';


export enum ActionType {
  Start = 'START',
  Stop = 'STOP',
  Restart = 'RESTART'
}

export interface IEventData {
  service: IQueryService,
  actionType: ActionType
}

export type modalData = {
  serviceName: string
  actionType: ActionType
  password: string
} 
@Component({
  selector: 'vdi-service-page',
  templateUrl: './service-page.component.html',
  styleUrls: ['./service-page.component.scss']
})
export class ServicePageComponent implements OnInit {

  public services: IQueryService[];

  constructor(private servicePageService: ServicePageService, private waitService: WaitService, private dialog: MatDialog) { }

  public ngOnInit(): void {

    this.waitService.setWait(true);
    this.getAllServices();

  }

  public getAllServices(): void {  
    this.waitService.setWait(true);   
    this.servicePageService.getServicesInfo().valueChanges.subscribe((res: ApolloQueryResult<IQueryResponse>) => {
      const services = res.data.services;
      const mapper = new ServicePageMapper();
      this.services = services.map(((service: IQueryApiModel) => mapper.serverQueryModelToClientModel(service)));
      this.waitService.setWait(false);      
    });
  }

  public refresh(): void {
    this.getAllServices();
  }

  public clickControls(event: IEventData): void  {
    const dialogRef  = this.dialog.open(ConfirmModalComponent, {
      autoFocus: true,
      width: '500px',
      data: {
        serviceName: event.service.serviceName,
        actionType: event.actionType
      }
    });
    
    dialogRef.afterClosed().subscribe( (result: MutationServiceInfo | undefined) => {

      if (!result){
        return;
      }      
      this.services = this.services.map((service: IQueryService) => {

      if (service.serviceName === event.service.serviceName){

        service.status = result.status
      }

      return service;
    })
   
    })
  }
}
