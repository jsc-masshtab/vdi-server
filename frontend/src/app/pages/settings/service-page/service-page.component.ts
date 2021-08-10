import { Component, OnInit } from '@angular/core';
import { ApolloQueryResult } from 'apollo-client';

import { WaitService } from '@core/components/wait/wait.service';

import { IQueryApiModel, IQueryResponse, IQueryService, ServicePageMapper } from './service-page.mapper';
import { ServicePageService } from './service-page.service';

@Component({
  selector: 'vdi-service-page',
  templateUrl: './service-page.component.html',
  styleUrls: ['./service-page.component.scss']
})
export class ServicePageComponent implements OnInit {

  public services: IQueryService[];

  public servicesCollection: ReadonlyArray<object> = [
    {
      title: 'Название',
      property: 'verboseName',
      class: 'name-start',
      icon: 'desktop',
      type: 'string',
      sort: true
    },
    {
      title: 'Cтатус',
      property: 'status',
      sort: true
    }
  ];
  constructor(private servicePageService: ServicePageService, private waitService: WaitService) { }

  public ngOnInit(): void {

    this.waitService.setWait(true);
    this.getAllServices();

  }

  public getAllServices(): void {  
    this.servicePageService.getServicesInfo().valueChanges.subscribe((res: ApolloQueryResult<IQueryResponse>) => {
      const services = res.data.services;
      const mapper = new ServicePageMapper();
      this.services = services.map(((service: IQueryApiModel) => mapper.serverQueryModelToClientModel(service)));
      this.waitService.setWait(false);      
    });
  }



}
