import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { modalData } from './service-page.component';
import { IMutationResponse, IQueryResponse } from './service-page.mapper';

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
              service_name
              verbose_name
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
        mutation settings($password: ShortString, $serviceName: ShortString, $actionType: ServiceAction) {
        doServiceAction(sudo_password:$password, service_name: $serviceName, service_action: $actionType){
           ok,
           service_status
         }
      }`,
      variables: {
        method: 'POST',
        password: data.password,
        serviceName: data.serviceName,
        actionType: data.actionType

      }
    })
  }

}
