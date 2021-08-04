import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';  



export interface ISystemResponse{
  data: ISystemData
}

export interface ISystemData {
  networksList: Network[]
  timezone: string
  date: Date
}

type Network = {
  name: string
  ip: string
}


@Injectable({
  providedIn: 'root'
})
export class SystemService {

  constructor(private appolo: Apollo) { }

  public getSystemInfo(): QueryRef<any, any> {
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
