import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class NodesService {

    constructor(private service: Apollo) {}

    public getAllNodes(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query allNodes {
                            controllers {
                                nodes {
                                    id
                                    verbose_name
                                    status
                                    datacenter_id
                                    datacenter_name
                                    cpu_count
                                    memory_count
                                    management_ip
                                    cluster {
                                        verbose_name
                                        id
                                    }
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        });
    }

    public getNode(nodeId: string): QueryRef<any, any> {
        const idNode = nodeId;
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
                id: idNode
            }
        });
    }
}

