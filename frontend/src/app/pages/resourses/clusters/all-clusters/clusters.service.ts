import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '../../../../shared/types';


@Injectable()
export class ClustersService  {

    public paramsForGetClusters: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllClusters(filter?, refresh?): QueryRef<any, any> {
        let query: string = `query resources($ordering:ShortString) {
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
            query = `query controllers($controller_id:UUID, $ordering:ShortString) {
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
        } else if (refresh && !filter) {
            query = `query resources($ordering: ShortString, $refresh: Boolean) {
                clusters(ordering: $ordering, refresh: $refresh) {
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
        }

        return  this.service.watchQuery({
            query: gql(query),
            variables: {
                method: 'GET',
                ordering: this.paramsForGetClusters.nameSort,
                ...filter,
                refresh
            }
        });
    }

    public getCluster(id: string, controller_address: string, refresh: boolean): QueryRef<any, any> {

        let query: string = ` query resources($id: UUID, $controller_address: UUID) {
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
                            }`

        if (refresh) {
          query = ` query resources($id: UUID, $controller_address: UUID, $refresh: Boolean) {
                      cluster(cluster_id: $id, controller_id: $controller_address, refresh: $refresh) {
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

