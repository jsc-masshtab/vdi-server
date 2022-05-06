import { Injectable } from '@angular/core';
import { IParams } from '@app/shared/types';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

export interface QueryParams {
    startDate: Date
    endDate: Date
    poolId?: string
}

export interface PoolStatisticsResponse {
    poolUsageStatistics: PoolStatistics        
}

export interface PoolStatistics {
    successful_conn_number: number
    disconn_number: number
    conn_err_number: number
    conn_duration_average: number
}

@Injectable()
export class PoolStatisticsService {

    constructor(private service: Apollo) { }
    
    public paramsForGetPools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    public getAllPools(): QueryRef<any, any> {

        return this.service.watchQuery({
            query: gql` 
                query pools($ordering:ShortString) {
                    pools(ordering: $ordering) {
                        pool_id
                        verbose_name
                    
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetPools.nameSort
            }
        });
    }


    getPoolStatistics(queryParams: QueryParams){
        return this.service.watchQuery({
            query: gql`
            query statistics($startDate: DateTime, $endDate: DateTime, $poolId: UUID){
                pool_usage_statistics(start_date: $startDate, end_date: $endDate, pool_id: $poolId){
                    successful_conn_number
                    disconn_number
                    conn_err_number
                    conn_duration_average
                    conn_errors(limit: 10, offset: 0) {
                        name
                        conn_number
                    }
                    used_pools_overall(limit: 10, offset: 0) {
                        name
                        conn_number
                    }
                    used_client_os(limit: 10, offset: 0) {
                        name
                        conn_number
                    }
                    used_client_versions(limit: 10, offset: 0) {
                        name
                        conn_number
                    }
                    users(limit: 10, offset: 0) {
                        name
                        conn_number
                    }
                    conn_number_by_time_interval {
                        time_interval
                        conn_number
                        percentage
                    }
                }
            }`,
            variables: {
                method: 'GET',
                ...queryParams
            }
        })
    }
}
