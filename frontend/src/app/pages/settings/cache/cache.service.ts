import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../shared/types';

@Injectable({
  providedIn: 'root'
})
export class CacheService {

  public paramsForGetUsers: IParams = {
    spin: true,
    nameSort: undefined
  };

  constructor(private service: Apollo) { }

  public getSettings(): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query settings {
          settings {
            REDIS_EXPIRE_TIME
          }
        }
      `,
      variables: {
        method: 'GET'
      }
    });
  }

  public changeSettings(data, fields) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation settings(
          $redis_expire_time: Int){
          changeSettings(
            REDIS_EXPIRE_TIME: $redis_expire_time
          ){
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        ...data,
        ...fields
      }
    });
  }

  public clearCache() {
    return this.service.mutate<any>({
      mutation: gql`
        mutation settings {
          clearRedisCache {
            ok
          }
        }
      `,
      variables: {
        method: 'POST'
      }
    });
  }
}
