import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class ServicePageService {

constructor(private apollo: Apollo) { }

public getServicesInfo(): QueryRef<any> {
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
}
