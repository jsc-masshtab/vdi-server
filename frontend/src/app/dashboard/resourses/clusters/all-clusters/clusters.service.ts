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

    public getAllClusters(): QueryRef<any, any> {

        return  this.service.watchQuery({
            query: gql` 
                query resources($ordering:String) {
                    clusters(ordering: $ordering) {
                        id
                        verbose_name
                        nodes_count
                        status
                        cpu_count
                        memory_count
                        controller {
                            id
                            verbose_name
                        }
                        
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetClusters.nameSort
            }
        });
    }

    public getCluster(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query: gql` query resources($id: UUID, $controller_address: UUID) {
                            cluster(cluster_id: $id, controller_id: $controller_address) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
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

