import { IParams } from './../../../../../types/index.d';
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class NodesService {

    constructor(private service: Apollo) {}

    public paramsForGetNodes: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    public getAllNodes(): QueryRef<any, any> {

        return  this.service.watchQuery({
            query:  gql` query allNodes($ordering:String, $reversed_order: Boolean) {
                            nodes(ordering: $ordering, reversed_order: $reversed_order) {
                                id
                                verbose_name
                                status
                                datacenter_name
                                cpu_count
                                memory_count
                                management_ip
                                cluster {
                                    verbose_name
                                }
                                controller {
                                    ip
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetNodes.nameSort,
                reversed_order: this.paramsForGetNodes.reverse
            }
        });
    }

    public getNode(id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query node($id: String) {
                            node(id: $id) {
                                verbose_name
                                status
                                cpu_count
                                memory_count
                                management_ip
                                cluster {
                                    verbose_name
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
                id
            }
        });
    }
}

