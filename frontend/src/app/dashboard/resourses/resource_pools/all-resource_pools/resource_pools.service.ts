import { IParams } from '../../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class ResourcePoolsService {

    public paramsForGetResourcePools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllResourcePools(filter?): QueryRef<any, any> {

        let query: string = `query resources($ordering:String) {
            resource_pools(ordering: $ordering) {
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
        }`

        if (filter) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $ordering:String) {
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
                ...filter
            }
        });
    }

    public getResourcePool(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
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
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}

