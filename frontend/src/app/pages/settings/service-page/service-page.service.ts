import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { modalData } from './service-page.component';


export enum Status {
  Running = 'running',
  Stoped = 'stoped',
  Failed = 'failed',
  Exited = 'exited'
}

export interface IMutationResponse {
  doServiceAction: IMutationServiceInfo
}

export interface IMutationServiceInfo {
  ok: boolean,
  serviceStatus: Status
}
export interface IQueryResponse{
  services: IQueryService[]
}
export interface IQueryService {
  serviceName: string
  verboseName: string
  status: Status
}

@Injectable({
  providedIn: 'root'
})
export class ServicePageService {

  constructor(private apollo: Apollo) { }

  public getServicesInfo(): QueryRef<IQueryResponse> {
    return  this.apollo.watchQuery({
        query:  gql`
        query settings {
          services{
              serviceName: service_name
              verboseName: verbose_name
              status
            }
          }
        `,
        variables: {
            method: 'GET'
        }
    });
  }

  public updateService(data: modalData) {
    return this.apollo.mutate<IMutationResponse>({
      mutation: gql`
        mutation settings( $serviceName: ShortString, $actionType: ServiceAction) {
        doServiceAction( service_name: $serviceName, service_action: $actionType){
           ok,
           serviceStatus:service_status
         }
      }`,
      variables: {
        method: 'POST',
        serviceName: data.serviceName,
        actionType: data.actionType

      }
    })
  }

}
