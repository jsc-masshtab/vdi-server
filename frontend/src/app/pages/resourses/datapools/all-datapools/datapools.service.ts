import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../../../../types';


@Injectable()
export class DatapoolsService {

    public paramsForGetDatapools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllDatapools(filter?): QueryRef<any, any> {

        let query: string = `query resources($ordering:String) {
                datapools(ordering: $ordering) {
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
        `

        if (filter) {
            query = `query controllers($controller_id:UUID, $cluster_id: UUID, $resource_pool_id: UUID, $node_id: UUID, $ordering:String) {
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
                ...filter
            }
        });
    }

    public getDatapool(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
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


