import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../shared/types';

@Injectable({
  providedIn: 'root'
})
export class LogSettingService {

  public paramsForGetUsers: IParams = {
    spin: true,
    nameSort: undefined
  };

  constructor(private service: Apollo) { }

  public getSettings(): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql` 
        query events {
          journal_settings {
            period
            by_count
            count
            dir_path
          }
        }
      `,
      variables: {
        method: 'GET'
      }
    });
  }

  public changeJournalSettings(data, fields) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation events(
          $count: Int,
          $period: String,
          $by_count: Boolean,
          $dir_path: String){
          changeJournalSettings(
            count: $count,
            period: $period,
            by_count: $by_count,
            dir_path: $dir_path
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
}
