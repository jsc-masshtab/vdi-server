import { IParams } from '../../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class ClustersService  {

    public paramsForGetClusters: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllClusters(filter?): QueryRef<any, any> {

        let query: string = `query resources($ordering:String) {
            clusters(ordering: $ordering) {
                id
                verbose_name
                nodes_count
                status
                cpu_count
                memory_count
                description
                controller {
                    id
                    verbose_name
                }

            }
        }`

        if (filter) {
            query = `query controllers($controller_id:UUID, $ordering:String) {
                controller(id_:$controller_id) {
                    id
                    clusters(ordering: $ordering) {
                        id
                        verbose_name
                        status
                        cpu_count
                        memory_count
                        nodes_count
                        description
                    }
                }
            }`
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.paramsForGetClusters.nameSort,
                ...filter
            }
        });
    }

    public getCluster(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            cluster(cluster_id: $id, controller_id: $controller_address) {
                                id
                                verbose_name
                                description
                                status
                                cpu_count
                                memory_count
                                cluster_fs_configured
                                cluster_fs_type
                                nodes {
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

