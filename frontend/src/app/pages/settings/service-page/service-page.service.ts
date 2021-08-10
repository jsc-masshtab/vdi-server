import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IQueryResponse } from './service-page.mapper';

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


  addRdsPool(data) {
    let query: string = ` mutation
  settings {
    doServiceAction(sudo_password:"555", service_name: "apache2.service", service_action: RESTART)
      {
          ok,
          service_status
      }
}
    `;

    return this.service.mutate<any>({
        mutation: gql(query),
        variables: {
            method: 'POST',
            ...data
        }
    });
}
}
