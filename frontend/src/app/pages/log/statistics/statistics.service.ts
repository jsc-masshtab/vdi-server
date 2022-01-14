import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


// interface IDate {
//     month?: number
//     year: number
// } 
@Injectable()
export class StatisticsService {

    constructor(private apollo: Apollo) { }

    public getStatistics(): QueryRef<any> {
        return this.apollo.watchQuery({
          query: gql`
            query statistics {
              data {
                  web_statistics_report
                }
            }
          `,
          variables: {
            method: 'GET',
          }
        });
      }
}

