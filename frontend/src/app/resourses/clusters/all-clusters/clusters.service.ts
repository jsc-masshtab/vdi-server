import { IParams } from './../../../../../types/index.d';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class ClustersService  {

    public paramsForGetClusters: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo) {}

    public getAllClusters(): QueryRef<any, any> {

        return  this.service.watchQuery({
            query:  gql` query allClusters($ordering:String, $reversed_order: Boolean) {
                            clusters(ordering: $ordering, reversed_order: $reversed_order) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                                controller {
                                    ip
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetClusters.nameSort,
                reversed_order: this.paramsForGetClusters.reverse
            }
        });
    }

    public getCluster(id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query cluster($id: String) {
                            cluster(id: $id) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                                nodes {
                                    verbose_name
                                    status
                                    cpu_count
                                    memory_count
                                    management_ip
                                }
                                datapools {
                                    used_space
                                    free_space
                                    size
                                    status
                                    type
                                    vdisk_count
                                    file_count
                                    iso_count
                                    verbose_name
                                }
                                templates {
                                    info
                                }
                                vms {
                                    name
                                    template {
                                        name
                                    }
                                    node {
                                        verbose_name
                                    }
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id: id
            }
        });
    }
}

