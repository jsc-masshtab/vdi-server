import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { ISystemResponse } from './system.mapper';


@Injectable({
  providedIn: 'root'
})
export class SystemService {

  constructor(private appolo: Apollo) { }

  public getSystemInfo(): QueryRef<ISystemResponse> {
    return this.appolo.watchQuery({
      query: gql` 
        query settings {
          system_info {
            networks_list{
              name
              ipv4
            }
            time_zone
            local_time
          }
        }
      `,
      variables: {
        method: 'GET'
      }
    });
  }
}
