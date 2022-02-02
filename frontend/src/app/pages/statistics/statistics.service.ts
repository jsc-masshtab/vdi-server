import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


export interface ApiResponse {
  statisticsReport: string
}
export interface IDate {
    month?: number
    year?: number
} 
@Injectable()
export class StatisticsService {

    constructor(private apollo: Apollo) { }

    public getStatistics(date: IDate): QueryRef<ApiResponse> {
        return this.apollo.watchQuery({
          query: gql`
            query statistics($month: Int, $year: Int) {
                  statisticsReport:web_statistics_report( year: $year, month: $month)   
            }
          `,
          variables: {
            method: 'GET',
            ...date
          }
        });
      }

}

