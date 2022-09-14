import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../../shared/types';


@Injectable()
export class ResourcePoolsService {

    public paramsForGetResourcePools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllResourcePools(filter?, refresh?): QueryRef<any, any> {

        let query: string = `
            query resources(
                $limit: Int,
                $offset: Int,
                $ordering:ShortString
            ){
                resource_pools_with_count(
                    limit: $limit,
                    offset: $offset,
                    ordering: $ordering
                ){
                    count
                    resource_pools {
                        id
                        verbose_name
                        domains_count
                        cpu_limit
                        memory_limit
                        controller {
                            id
                            verbose_name
                            address
                        }
                    }
                }
            }
        `

        if (filter.controller_id) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $ordering:ShortString) {
                controller(id_:$controller_id) {
                    id
                    resource_pools(cluster_id: $cluster_id, ordering: $ordering) {
                        id
                        verbose_name
                        domains_count
                        cpu_limit
                        memory_limit
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.paramsForGetResourcePools.nameSort,
                ...filter,
                refresh
            }
        });
    }

    public getResourcePool(id: string, controller_address: string, refresh: boolean): QueryRef<any, any> {

        let query: string = ` query resources($id: UUID, $controller_address: UUID) {
                                resource_pool(resource_pool_id: $id, controller_id: $controller_address) {
                                    id
                                    verbose_name
                                    description
                                    cpu_limit
                                    memory_limit
                                    nodes_cpu_count
                                    domains_cpu_count
                                    nodes_memory_count
                                    domains_memory_count
                                    controller {
                                        id
                                        address
                                    }
                                }
                            }`

        if (refresh) {
          query = ` query resources($id: UUID, $controller_address: UUID, $refresh: Boolean) {
                      resource_pool(resource_pool_id: $id, controller_id: $controller_address, refresh: $refresh) {
                          id
                          verbose_name
                          description
                          cpu_limit
                          memory_limit
                          nodes_cpu_count
                          domains_cpu_count
                          nodes_memory_count
                          domains_memory_count
                          controller {
                              id
                              address
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

