import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../../shared/types';


@Injectable()
export class DatapoolsService {

    public paramsForGetDatapools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllDatapools(filter?, refresh?): QueryRef<any, any> {

        let query: string = `
            query resources(
                $limit: Int,
                $offset: Int,
                $ordering:ShortString
            ){
                datapools_with_count(
                    limit: $limit,
                    offset: $offset,
                    ordering: $ordering
                ){
                    count
                    datapools {
                        id
                        used_space
                        free_space
                        status
                        type
                        verbose_name
                        controller {
                            id
                            verbose_name
                        }
                    }
                }
            }
        `

        if (filter.controller_id) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $resource_pool_id: UUID, $node_id: UUID, $ordering:ShortString) {
                controller(id_:$controller_id) {
                    id
                    data_pools(cluster_id: $cluster_id, resource_pool_id: $resource_pool_id, node_id: $node_id, ordering: $ordering) {
                        id
                        used_space
                        free_space
                        status
                        type
                        verbose_name
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.paramsForGetDatapools.nameSort,
                ...filter,
                refresh
            }
        });
    }

    public getDatapool(id: string, controller_address: string, refresh: boolean): QueryRef<any, any> {

        let query: string = ` query resources($id: UUID, $controller_address: UUID) {
                                datapool(datapool_id: $id, controller_id: $controller_address) {
                                    used_space
                                    free_space
                                    description
                                    size
                                    status
                                    type
                                    verbose_name
                                    nodes_connected {
                                        id
                                        verbose_name
                                        status
                                    }
                                }
                            }`

        if (refresh) {
          query = ` query resources($id: UUID, $controller_address: UUID, $refresh: Boolean) {
                      datapool(datapool_id: $id, controller_id: $controller_address, refresh: $refresh) {
                          used_space
                          free_space
                          description
                          size
                          status
                          type
                          verbose_name
                          nodes_connected {
                              id
                              verbose_name
                              status
                          }
                      }
                  }`
        }
        return this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                id,
                controller_address,
                refresh
            }
        });
    }
}


