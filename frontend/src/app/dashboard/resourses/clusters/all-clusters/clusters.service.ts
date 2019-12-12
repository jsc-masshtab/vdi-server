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
            query:  gql` query resources($ordering:String) {
                            clusters(ordering: $ordering) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                                controller {
                                    address
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
            query:  gql` query resources($id: String, $controller_address: String) {
                            cluster(id: $id, controller_address: $controller_address) {
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
                                    verbose_name
                                }
                                vms {
                                    verbose_name
                                    template {
                                        verbose_name
                                    }
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

